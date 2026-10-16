"""Design-space model of a small edge accelerator running ViT-Tiny.

The chip: a square output-stationary MAC array, one on-chip SRAM buffer, a
small 4-lane SIMD host core for everything the array cannot do, optional
softmax and GELU units with a chosen number of lanes, and a narrow DRAM link.

Modelling choices (all deliberate simplifications, stated so they can be
argued with):

* GEMM cycles come from archsim.systolic (OS dataflow, tiles do not overlap).
* Within an operator, DRAM transfers overlap with compute: an operator takes
  max(compute cycles, DRAM cycles). Operators run one after the other.
* GEMM tiling is a simple heuristic (see _gemm_dram_bytes); Lab 1 shows that
  a proper search does better.
* An element-wise operator whose input fits in half the buffer is fused with
  its producer and costs no DRAM traffic.
* Weights are always streamed from DRAM: 5.3 MB of ViT-Tiny weights do not fit
  in any buffer this area budget allows.
* Accuracy is not modelled. 4-bit designs are flagged, not penalised.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
import json
import math

import numpy as np

from . import energy, systolic
from .nonlinear import OpCounter, softmax_ibert, gelu_ibert
from .workloads import VIT_TINY, vit_block

FREQ_HZ = 50e6
DRAM_BYTES_PER_CYCLE = 8          # 0.4 GB/s at 50 MHz
HOST_LANES = 4
HOST_INSTR_PJ = 5.0               # assumed fetch/decode energy per SIMD instruction
HOST_AREA_MM2 = 0.10              # assumed small 32-bit core with FPU
LEAK_MW_PER_MM2 = 0.1             # assumed
ARRAY_OVERHEAD = 1.10             # wiring and control around the PEs
AREA_BUDGET_MM2 = 1.0
POWER_BUDGET_MW = 1.0
UNIT_BITS = 16                    # non-linear units work on 16-bit integers
SUBMISSION_VERSION = 1

# Cycles the host needs per complex primitive (8 fmul + 8 fadd for exp, ...).
_HOST_CYCLES = {op: nm + na for op, (nm, na) in energy.COMPLEX_AS_FP32.items()}


@dataclass(frozen=True)
class Design:
    array: int = 16            # the MAC array is array x array PEs
    buffer_kib: int = 128
    bits: int = 8              # weight and activation precision: 4, 8 or 16
    softmax_lanes: int = 0     # 0 means no softmax unit; softmax runs on the host
    gelu_lanes: int = 0

    def validate(self) -> None:
        if not 1 <= self.array <= 64:
            raise ValueError("array must be between 1 and 64")
        if not 4 <= self.buffer_kib <= 4096:
            raise ValueError("buffer_kib must be between 4 and 4096")
        if self.bits not in (4, 8, 16):
            raise ValueError("bits must be 4, 8 or 16")
        if not (0 <= self.softmax_lanes <= 64 and 0 <= self.gelu_lanes <= 64):
            raise ValueError("unit lanes must be between 0 and 64")


def _unit_lane_ops(fn) -> dict:
    ops = OpCounter()
    fn(np.zeros((1, 64)), ops=ops)
    return ops.per_element(64)


SOFTMAX_LANE_OPS = _unit_lane_ops(softmax_ibert)
GELU_LANE_OPS = _unit_lane_ops(gelu_ibert)


def _lane_area_um2(per_elem: dict) -> float:
    a = energy.AREA_UM2
    muls = per_elem.get("mul", 0)
    others = sum(v for k, v in per_elem.items() if k not in ("mul", "div"))
    regs = 64 * energy.FLIPFLOP_UM2_PER_BIT
    return math.ceil(muls) * a[("mul", 16)] + math.ceil(others) * a[("add", 32)] + regs


def area_breakdown(d: Design) -> dict:
    um2 = 1e-6
    return {
        "pe_array": d.array ** 2 * energy.pe_area_um2(d.bits) * ARRAY_OVERHEAD * um2,
        "buffer": energy.sram_area_mm2(d.buffer_kib),
        "host": HOST_AREA_MM2,
        # each unit also has one shared 32-bit divider for the per-row reciprocal
        "softmax_unit": (d.softmax_lanes * _lane_area_um2(SOFTMAX_LANE_OPS)
                         + (d.softmax_lanes > 0) * energy.AREA_UM2[("mul", 32)]) * um2,
        "gelu_unit": d.gelu_lanes * _lane_area_um2(GELU_LANE_OPS) * um2,
    }


def _gemm_dram_bytes(M: int, K: int, N: int, b: float, buf: float) -> float:
    """Heuristic tiling, not a search: the cheapest of three simple schedules.

    1. One operand fits in half the buffer: keep it, stream the other once.
    2. Otherwise: T x T output tiles with full-K panels of A and B on chip,
       T the largest power of two that fits.
    """
    once = b * (M * K + K * N + M * N)
    if min(M * K, K * N) * b <= buf / 2:
        return once
    T = 1
    while 2 * T <= max(M, N) and b * 2 * (2 * T) * K + 4 * (2 * T) ** 2 <= buf:
        T *= 2
    if b * 2 * T * K + 4 * T * T > buf:      # not even a 1 x 1 tile with full-K panels
        return b * 2 * M * K * N + b * M * N
    a_reads = 1 if T >= N else math.ceil(N / T)
    b_reads = 1 if T >= M else math.ceil(M / T)
    return b * (M * K * a_reads + K * N * b_reads + M * N)


def evaluate(d: Design, seq: int = VIT_TINY["seq"], depth: int = VIT_TINY["depth"],
             fps: float = 1.0) -> dict:
    """Latency, energy, area and power for one ViT-Tiny inference (``depth`` blocks)."""
    d.validate()
    b = d.bits / 8
    buf = d.buffer_kib * 1024
    R = C = d.array
    cyc = {"gemm": 0.0, "softmax": 0.0, "gelu": 0.0, "other": 0.0}
    e = {"mac": 0.0, "sram": 0.0, "dram": 0.0, "nonlinear": 0.0}
    for op in vit_block(seq, VIT_TINY["dim"], VIT_TINY["heads"], VIT_TINY["mlp_ratio"]):
        if op.is_gemm:
            M, K, N = op.shape
            g = systolic.gemm(M, K, N, R, C, "os")
            dram = op.count * _gemm_dram_bytes(M, K, N, b, buf)
            sram = op.count * b * (M * K * math.ceil(N / C) + K * N * math.ceil(M / R) + M * N)
            cyc["gemm"] += max(op.count * g["cycles"], dram / DRAM_BYTES_PER_CYCLE)
            e["mac"] += op.macs * energy.mac_energy(d.bits)
            e["sram"] += energy.sram_energy(sram + dram, buf)
            e["dram"] += energy.dram_energy(dram)
            continue
        n = op.elements
        fused = op.shape[0] * op.shape[1] * b <= buf / 2
        dram = 0.0 if fused else op.bytes(d.bits)
        lanes = {"softmax": d.softmax_lanes, "gelu": d.gelu_lanes}.get(op.kind, 0)
        if lanes:
            per = SOFTMAX_LANE_OPS if op.kind == "softmax" else GELU_LANE_OPS
            c = n / lanes
            e["nonlinear"] += n * energy.primitive_energy(per, UNIT_BITS)
        else:
            prim = op.primitive_ops()
            host_ops = sum(v * _HOST_CYCLES.get(k, 1) for k, v in prim.items())
            c = host_ops / HOST_LANES
            e["nonlinear"] += energy.primitive_energy(prim, 32) + c * HOST_INSTR_PJ
        key = op.kind if op.kind in cyc else "other"
        cyc[key] += max(c, dram / DRAM_BYTES_PER_CYCLE)
        e["dram"] += energy.dram_energy(dram)
        e["sram"] += energy.sram_energy(2 * op.bytes(d.bits), buf)

    cyc = {k: v * depth for k, v in cyc.items()}
    e = {k: v * depth * 1e-6 for k, v in e.items()}          # pJ -> uJ
    area = area_breakdown(d)
    area_total = sum(area.values())
    latency_s = sum(cyc.values()) / FREQ_HZ
    leak_mw = LEAK_MW_PER_MM2 * area_total
    e["leakage"] = leak_mw * 1e-3 * latency_s * 1e6
    energy_uj = sum(e.values())
    if latency_s > 1 / fps:
        power_mw = float("nan")                               # cannot sustain the frame rate
    else:
        power_mw = energy_uj * 1e-6 * fps * 1e3 + leak_mw * (1 - latency_s * fps)
    return dict(
        latency_ms=latency_s * 1e3, energy_uj=energy_uj, area_mm2=area_total,
        power_mw=power_mw, fps=fps, within_budget=area_total <= AREA_BUDGET_MM2,
        fps_at_1mw=_fps_at_budget(energy_uj, leak_mw, latency_s),
        energy_breakdown_uj=e, cycles_breakdown=cyc, area_breakdown_mm2=area,
        notes=["4-bit: check accuracy before trusting this point"] if d.bits == 4 else [],
    )


def _fps_at_budget(energy_uj: float, leak_mw: float, latency_s: float) -> float:
    """Highest frame rate that keeps average power under POWER_BUDGET_MW."""
    spare_mw = POWER_BUDGET_MW - leak_mw
    if spare_mw <= 0:
        return 0.0
    # P = E * fps + leak * (1 - latency * fps)  =>  solve P = budget for fps
    return min(spare_mw / (energy_uj * 1e-3 - leak_mw * latency_s), 1 / latency_s)


def make_submission(team: str, d: Design, **eval_kwargs) -> dict:
    m = evaluate(d, **eval_kwargs)
    keep = ("latency_ms", "energy_uj", "area_mm2", "power_mw", "fps_at_1mw", "within_budget")
    return dict(version=SUBMISSION_VERSION, team=team, design=asdict(d),
                metrics={k: m[k] for k in keep})


def save_submission(sub: dict, path: str = "submission.json") -> str:
    with open(path, "w") as f:
        json.dump(sub, f, indent=2)
    return path


def load_submission(path: str) -> dict:
    """Read a submission and recompute its metrics from the design it declares."""
    with open(path) as f:
        sub = json.load(f)
    d = Design(**sub["design"])
    return make_submission(sub["team"], d)

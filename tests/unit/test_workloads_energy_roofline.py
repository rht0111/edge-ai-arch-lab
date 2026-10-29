import math

import numpy as np
import pytest

from archsim import energy, roofline, workloads


def test_vit_tiny_block_shapes_and_macs():
    ops = workloads.vit_block()
    by_name = {op.name: op for op in ops}
    assert by_name["qkv"].shape == (197, 192, 576)
    assert by_name["scores"].count == 3
    # 4 * S * D^2 (qkv + proj) + 2 * S^2 * D (attention) + 2 * S * D * 4D (MLP)
    s, d = 197, 192
    expected = 4 * s * d * d + 2 * s * s * d + 8 * s * d * d
    assert sum(op.macs for op in ops) == expected


def test_vit_tiny_weight_count():
    # 12 * D^2 per block, so 12 blocks give ~5.3 M GEMM weights (ViT-Tiny has 5.7 M in total)
    assert workloads.weight_count(workloads.vit_block()) == 12 * 192 * 192


def test_gemm_bytes_and_intensity():
    op = workloads.Op("g", "gemm", (4, 8, 2))
    assert op.flops == 2 * 4 * 8 * 2
    assert op.bytes(8) == 4 * 8 + 8 * 2 + 4 * 2
    assert op.bytes(16) == 2 * op.bytes(8)
    assert op.intensity(8) == pytest.approx(128 / 56)


def test_elementwise_counts():
    sm = workloads.Op("sm", "softmax", (10, 10), count=2)
    assert sm.primitive_ops()["exp"] == 200
    ln = workloads.Op("ln", "layernorm", (10, 4))
    assert ln.primitive_ops()["rsqrt"] == 10
    add = workloads.Op("a", "add", (3, 3), n_inputs=2)
    assert add.bytes(8) == 27


def test_attention_grows_quadratically():
    def attn_flops(seq):
        return sum(op.flops for op in workloads.vit_block(seq=seq) if op.name in ("scores", "context"))
    assert attn_flops(1024) / attn_flops(64) == pytest.approx(256)


def test_summary_percentages_sum_to_100():
    rows = workloads.summary(workloads.vit_block())
    assert sum(r["flops_pct"] for r in rows) == pytest.approx(100)
    assert sum(r["bytes_pct"] for r in rows) == pytest.approx(100)


def test_horowitz_points():
    assert energy.mac_energy(8) == pytest.approx(0.3)
    assert energy.sram_energy(8, 8192) == pytest.approx(10)
    assert energy.sram_energy(8, 32 * 1024) == pytest.approx(20)
    # the sqrt fit should be within 15% of the 1 MB point (100 pJ)
    assert energy.sram_energy(8, 1 << 20) == pytest.approx(100, rel=0.15)
    assert energy.dram_energy(8) == pytest.approx(1300)


def test_energy_ordering():
    # the point of the table is DRAM >> SRAM >> arithmetic
    assert energy.dram_energy(1) > 10 * energy.sram_energy(1, 256 * 1024)
    assert energy.sram_energy(1, 64 * 1024) > energy.mac_energy(8)
    assert energy.op_energy("exp") > 5 * energy.op_energy("fmul", 32)


def test_primitive_energy_and_area():
    assert energy.primitive_energy({"add": 10}, 8) == pytest.approx(0.3)
    assert energy.pe_area_um2(16) > energy.pe_area_um2(8) > energy.pe_area_um2(4)
    assert energy.sram_area_mm2(64) == pytest.approx(0.32)


def test_roofline():
    m = roofline.Machine("m", peak_ops=100.0, bandwidth=10.0)
    assert m.ridge == 10
    assert m.attainable(1) == pytest.approx(10)
    assert m.attainable(1000) == pytest.approx(100)
    assert m.bound(5) == "memory" and m.bound(20) == "compute"
    assert roofline.EDGE_NPU.ridge == pytest.approx(64)
    assert np.allclose(m.attainable([1, 100]), [10, 100])
    assert not math.isnan(roofline.accelerator().peak_ops)

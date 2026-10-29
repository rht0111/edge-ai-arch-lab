"""Energy and area per operation and per memory access.

ILLUSTRATIVE NUMBERS. The arithmetic and memory figures are the 45 nm, 0.9 V
values popularised by M. Horowitz, "Computing's energy problem (and what we
can do about it)", ISSCC 2014. Entries marked "assumed" or "interpolated" are
not in that table. They are our own rough estimates, chosen to be plausible
and to keep the ratios right. Use them to compare designs with each other,
never as absolute predictions for a real chip. See docs/references.md.
"""

from __future__ import annotations

import math

# --- Arithmetic energy, pJ per operation ---------------------------------
# Keys are (operation, bits). "add" and "mul" are integer, "fadd" and "fmul" floating point.
OP_PJ = {
    ("add", 8): 0.03, ("add", 16): 0.05, ("add", 32): 0.1,
    ("mul", 8): 0.2, ("mul", 32): 3.1,
    ("mul", 16): 0.8,   # interpolated, multiplier energy grows ~ bits^2
    ("mul", 4): 0.05,   # interpolated, same rule
    ("add", 4): 0.02,   # assumed
    ("fadd", 16): 0.4, ("fadd", 32): 0.9,
    ("fmul", 16): 1.1, ("fmul", 32): 3.7,
}

# --- Area, um^2 per unit (same source, 4/16-bit multipliers interpolated) --
AREA_UM2 = {
    ("add", 8): 36, ("add", 16): 67, ("add", 32): 137,
    ("mul", 8): 282, ("mul", 32): 3495,
    ("mul", 16): 1130, ("mul", 4): 70, ("add", 4): 20,
    ("fadd", 16): 1360, ("fadd", 32): 4184,
    ("fmul", 16): 1640, ("fmul", 32): 7700,
}
FLIPFLOP_UM2_PER_BIT = 4.5   # assumed, 45 nm standard-cell DFF
SRAM_MM2_PER_KIB = 0.005     # assumed, ~0.35 um^2 6T cell plus ~40% periphery

# --- Memory energy, pJ per 64-bit access ----------------------------------
# Horowitz gives 10 pJ (8 KB), 20 pJ (32 KB) and 100 pJ (1 MB) SRAM reads.
# 10 pJ * sqrt(size / 8 KB) fits all three points within ~15%, so we use it.
SRAM_PJ_8KB = 10.0
DRAM_PJ_64B = 1300.0         # low end of the 1.3-2.6 nJ range quoted for DRAM

# Cost of the "expensive" primitives in terms of FP32 mul/add, assumed for a
# software or iterative implementation (range reduction + polynomial, or
# Newton iterations). Used for the float reference path only.
COMPLEX_AS_FP32 = {
    "exp": (8, 8),     # (fmul count, fadd count)
    "tanh": (10, 10),
    "div": (6, 3),
    "rsqrt": (6, 3),
}


def op_energy(op: str, bits: int = 32) -> float:
    """Energy in pJ of one primitive operation.

    ``op`` is one of add, mul, fadd, fmul, cmp, shift, floor, lut, mac, or one
    of the complex primitives exp, tanh, div, rsqrt (always costed in FP32).
    """
    if op in COMPLEX_AS_FP32:
        nm, na = COMPLEX_AS_FP32[op]
        return nm * OP_PJ[("fmul", 32)] + na * OP_PJ[("fadd", 32)]
    if op in ("cmp", "shift", "floor"):   # assumed, about the cost of an adder
        return OP_PJ[("add", bits if ("add", bits) in OP_PJ else 32)]
    if op == "lut":                        # assumed, read of a tiny 32-byte table
        return sram_energy(1, 32)
    if op == "mac":
        return mac_energy(bits)
    return OP_PJ[(op, bits)]


def mac_energy(bits: int = 8) -> float:
    """One integer multiply plus a 32-bit accumulate, in pJ."""
    return OP_PJ[("mul", bits)] + OP_PJ[("add", 32)]


def sram_energy(n_bytes: float, size_bytes: float) -> float:
    """Energy in pJ to access ``n_bytes`` from an SRAM of ``size_bytes``."""
    per_word = SRAM_PJ_8KB * math.sqrt(size_bytes / 8192)
    return n_bytes / 8 * per_word


def dram_energy(n_bytes: float) -> float:
    """Energy in pJ to move ``n_bytes`` to or from off-chip DRAM."""
    return n_bytes / 8 * DRAM_PJ_64B


def primitive_energy(counts: dict, bits: int = 32) -> float:
    """Total pJ for a dict of primitive counts, e.g. Op.primitive_ops()."""
    return sum(n * op_energy(op, bits) for op, n in counts.items())


def pe_area_um2(bits: int = 8) -> float:
    """A MAC processing element, made of a multiplier, a 32-bit adder and their registers."""
    regs = (2 * bits + 32) * FLIPFLOP_UM2_PER_BIT
    return AREA_UM2[("mul", bits)] + AREA_UM2[("add", 32)] + regs


def sram_area_mm2(kib: float) -> float:
    return kib * SRAM_MM2_PER_KIB


def energy_table(bits: int = 8) -> list[tuple[str, float]]:
    """Rows for the 'cost of one event' table shown in Lab 0."""
    return [
        (f"int{bits} MAC", mac_energy(bits)),
        ("fp32 multiply", OP_PJ[("fmul", 32)]),
        ("fp32 exp (sw)", op_energy("exp")),
        ("SRAM 8 KiB, 1 byte", sram_energy(1, 8 * 1024)),
        ("SRAM 256 KiB, 1 byte", sram_energy(1, 256 * 1024)),
        ("DRAM, 1 byte", dram_energy(1)),
    ]

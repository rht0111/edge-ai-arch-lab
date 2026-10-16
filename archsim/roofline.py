"""Roofline model (Williams, Waterman and Patterson, CACM 2009).

Attainable performance = min(peak compute, bandwidth x arithmetic intensity).
Intensity is operations per byte moved across the memory interface we care
about, here off-chip DRAM.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Machine:
    name: str
    peak_ops: float      # operations per second (1 MAC = 2 operations)
    bandwidth: float     # bytes per second

    @property
    def ridge(self) -> float:
        """Intensity (ops/byte) at which the machine stops being memory-bound."""
        return self.peak_ops / self.bandwidth

    def attainable(self, intensity):
        return np.minimum(self.peak_ops, self.bandwidth * np.asarray(intensity, dtype=float))

    def bound(self, intensity: float) -> str:
        return "memory" if intensity < self.ridge else "compute"


def accelerator(rows: int = 16, cols: int = 16, freq_hz: float = 50e6,
                bandwidth: float = 0.4e9, name: str | None = None) -> Machine:
    """A MAC array clocked at ``freq_hz`` behind a DRAM link of ``bandwidth`` B/s."""
    peak = 2 * rows * cols * freq_hz
    return Machine(name or f"{rows}x{cols} @ {freq_hz / 1e6:g} MHz", peak, bandwidth)


# The toy edge accelerator used in the labs: 256 MACs at 50 MHz behind a
# narrow LPDDR interface. Peak 25.6 GOP/s, ridge at 64 ops/byte.
EDGE_NPU = accelerator(16, 16, 50e6, 0.4e9, name="edge NPU (16x16 @ 50 MHz, 0.4 GB/s)")


def plot(machine: Machine, points=(), ax=None, imin: float = 0.5, imax: float = 4096):
    """Draw the roofline and optional points.

    ``points`` is an iterable of (label, intensity) or (label, intensity, perf).
    Without a measured perf the point is drawn on the roof.
    """
    import matplotlib.pyplot as plt

    if ax is None:
        _, ax = plt.subplots(figsize=(6.5, 4))
    x = np.logspace(np.log10(imin), np.log10(imax), 200)
    ax.loglog(x, machine.attainable(x) / 1e9, color="black", lw=2, label=machine.name)
    ax.axvline(machine.ridge, color="grey", ls=":", lw=1)
    ax.text(machine.ridge * 1.08, machine.peak_ops / 1e9 * 0.04,
            f"ridge {machine.ridge:.0f} op/B", color="grey", rotation=90, va="bottom")
    for p in points:
        label, inten = p[0], p[1]
        perf = p[2] if len(p) > 2 else float(machine.attainable(inten))
        ax.plot(inten, perf / 1e9, "o")
        ax.annotate(label, (inten, perf / 1e9), textcoords="offset points",
                    xytext=(4, -10), fontsize=8)
    ax.set_xlabel("arithmetic intensity (ops / DRAM byte)")
    ax.set_ylabel("attainable performance (GOP/s)")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(loc="lower right", fontsize=8)
    return ax

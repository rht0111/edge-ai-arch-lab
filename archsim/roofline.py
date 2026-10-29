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
    Without a measured perf the point is drawn on the roof. Each point gets
    its own marker and a legend entry with its numbers, so labels never
    overlap even when points sit next to each other.
    """
    import matplotlib.pyplot as plt

    if ax is None:
        _, ax = plt.subplots(figsize=(9, 4.5))
    x = np.logspace(np.log10(imin), np.log10(imax), 200)
    ax.loglog(x, machine.attainable(x) / 1e9, color="black", lw=2)
    peak = machine.peak_ops / 1e9
    ax.text(imax, peak * 1.12, f"peak {peak:g} GOP/s", ha="right", va="bottom", fontsize=9)
    i_txt = imin * 2
    ax.text(i_txt, machine.bandwidth * i_txt / 1e9 * 1.25,
            f"DRAM {machine.bandwidth / 1e9:g} GB/s", rotation=0, fontsize=9, va="bottom")
    ax.axvline(machine.ridge, color="grey", ls=":", lw=1)
    ax.text(machine.ridge * 1.08, peak * 0.012, f"ridge\n{machine.ridge:.0f} op/B",
            color="grey", fontsize=8, va="bottom")
    markers = "osD^v<>pPhX*"
    for i, p in enumerate(points):
        label, inten = p[0], p[1]
        perf = p[2] if len(p) > 2 else float(machine.attainable(inten))
        ax.plot(inten, perf / 1e9, markers[i % len(markers)], ms=8, alpha=0.85,
                label=f"{label}: {inten:.1f} op/B, {perf / 1e9:.1f} GOP/s ({machine.bound(inten)})")
    ax.set_xlabel("arithmetic intensity (ops / DRAM byte)")
    ax.set_ylabel("attainable performance (GOP/s)")
    ax.set_ylim(top=peak * 3)
    ax.set_title(machine.name, fontsize=10)
    ax.grid(True, which="both", alpha=0.3)
    if points:
        ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1), fontsize=8, frameon=False)
    return ax

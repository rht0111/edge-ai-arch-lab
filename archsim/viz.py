"""Drawing helpers for the systolic-array notebook."""

from __future__ import annotations

import numpy as np

from .systolic import TileResult


def _fmt(v) -> str:
    return "" if np.isnan(v) else f"{v:g}"


def draw_frame(res: TileResult, t: int, ax=None, dataflow: str = "os"):
    """Draw the array at cycle ``t``: active PEs shaded, operands and accumulators printed."""
    import matplotlib.pyplot as plt

    f = res.frames[t]
    rows, cols = f["active"].shape
    if ax is None:
        _, ax = plt.subplots(figsize=(1.1 * cols + 1, 1.1 * rows + 0.6))
    ax.clear()
    for r in range(rows):
        for c in range(cols):
            y = rows - 1 - r
            busy = f["active"][r, c]
            ax.add_patch(plt.Rectangle((c, y), 0.94, 0.94, color="tab:orange" if busy else "0.92"))
            if dataflow == "os":
                top = f"a={_fmt(f['a'][r, c])}  b={_fmt(f['b'][r, c])}"
                bottom = f"acc={f['acc'][r, c]:g}"
            else:
                top = f"x={_fmt(f['x'][r, c])}  w={f['w'][r, c]:g}"
                bottom = f"psum={f['psum'][r, c]:g}"
            ax.text(c + 0.47, y + 0.62, top, ha="center", fontsize=7)
            ax.text(c + 0.47, y + 0.25, bottom, ha="center", fontsize=8, weight="bold")
    busy = int(f["active"].sum())
    ax.set_title(f"cycle {t + 1}/{res.cycles}: {busy}/{rows * cols} PEs busy")
    ax.set_xlim(-0.1, cols); ax.set_ylim(-0.1, rows); ax.set_aspect("equal"); ax.axis("off")
    return ax


def array_widget(res: TileResult, dataflow: str = "os"):
    """Slider (with play button) over the cycles of a traced tile simulation."""
    import ipywidgets as w
    import matplotlib.pyplot as plt

    play = w.Play(min=0, max=res.cycles - 1, interval=600)
    slider = w.IntSlider(min=0, max=res.cycles - 1, description="cycle")
    w.jslink((play, "value"), (slider, "value"))

    def show(t):
        draw_frame(res, t, dataflow=dataflow)
        plt.show()

    out = w.interactive_output(show, {"t": slider})
    return w.VBox([w.HBox([play, slider]), out])


def busy_plot(res: TileResult, ax=None):
    """Number of busy PEs per cycle: fill, steady state, drain."""
    import matplotlib.pyplot as plt

    if ax is None:
        _, ax = plt.subplots(figsize=(6, 2.5))
    rows, cols = res.frames[0]["active"].shape
    ax.step(range(1, res.cycles + 1), [f["active"].sum() for f in res.frames], where="mid")
    ax.axhline(rows * cols, color="grey", ls=":")
    ax.set_xlabel("cycle"); ax.set_ylabel("busy PEs")
    return ax

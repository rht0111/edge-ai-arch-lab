"""Load the student functions from a lab notebook so pytest can check them.

Only code cells tagged "task" are executed, in order, in a fresh namespace.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

LABS = Path(__file__).resolve().parent.parent / "labs"

# check name -> (notebook, function defined in it)
TASKS = {
    "lab0.gemm": ("lab0_profile", "gemm_flops_bytes"),
    "lab0.attention": ("lab0_profile", "attention_flops"),
    "lab0.breakdown": ("lab0_profile", "cost_breakdown"),
    "lab1.footprint": ("lab1_roofline_tiling", "footprint"),
    "lab1.traffic": ("lab1_roofline_tiling", "tiled_traffic"),
    "lab1.best": ("lab1_roofline_tiling", "best_tiling"),
    "lab2.ws_tile": ("lab2_systolic", "ws_tile_cycles"),
    "lab2.ws_gemm": ("lab2_systolic", "ws_gemm_cycles"),
    "lab3.lut_exp": ("lab3_nonlinear", "make_lut"),
    "lab3.lut_gelu": ("lab3_nonlinear", "make_lut"),
    "lab3.exp_shift": ("lab3_nonlinear", "exp_shift"),
    "lab3.softmax": ("lab3_nonlinear", "softmax_approx"),
    "lab4.pareto": ("lab4_design_challenge", "pareto_front"),
}


@lru_cache(maxsize=None)
def load(notebook: str) -> dict:
    nb = json.loads((LABS / f"{notebook}.ipynb").read_text())
    ns: dict = {"__name__": notebook}
    for cell in nb["cells"]:
        if cell["cell_type"] == "code" and "task" in cell.get("metadata", {}).get("tags", []):
            exec(compile("".join(cell["source"]), f"{notebook}.ipynb", "exec"), ns)
    return ns


def tasks_of(lab: str) -> list[str]:
    return [t for t in TASKS if t.startswith(lab + ".")]

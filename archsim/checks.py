"""Instant feedback for the lab notebooks.

``check("lab1.traffic", tiled_traffic)`` runs the student's function on fixed
inputs and compares the results with values stored in archsim/data/expected.json.
The reference code that produced those values is not part of this package.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

EXPECTED = Path(__file__).parent / "data" / "expected.json"
_ADAPTERS: dict = {}
_RTOL = 1e-6


def adapter(name: str):
    def register(fn):
        _ADAPTERS[name] = fn
        return fn
    return register


def _jsonable(v):
    if isinstance(v, dict):
        return {str(k): _jsonable(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_jsonable(x) for x in v]
    if isinstance(v, np.ndarray):
        return _jsonable(v.tolist())
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        return float(v)
    return v


def _close(got, exp, rtol) -> bool:
    if isinstance(exp, dict):
        return isinstance(got, dict) and got.keys() == exp.keys() and all(
            _close(got[k], exp[k], rtol) for k in exp)
    if isinstance(exp, list):
        return isinstance(got, list) and len(got) == len(exp) and all(
            _close(g, e, rtol) for g, e in zip(got, exp))
    if isinstance(exp, bool) or isinstance(exp, str) or exp is None:
        return got == exp
    if isinstance(exp, (int, float)):
        if not isinstance(got, (int, float)) or isinstance(got, bool):
            return False
        return math.isclose(got, exp, rel_tol=rtol, abs_tol=1e-9)
    return got == exp


def _short(v, n: int = 90) -> str:
    s = repr(v)
    return s if len(s) <= n else s[:n] + "..."


def run(name: str, fn) -> list:
    """Run ``fn`` on every input case of task ``name`` and return JSON-able results."""
    return _jsonable(_ADAPTERS[name](fn))


class Result:
    """Truthy when the check passed. Shows nothing when it is a cell's last value."""

    def __init__(self, ok: bool):
        self.ok = ok

    def __bool__(self) -> bool:
        return self.ok

    def _ipython_display_(self) -> None:
        pass

    def __repr__(self) -> str:
        return "PASS" if self.ok else "FAIL"


def check(name: str, fn, verbose: bool = True) -> Result:
    expected = json.loads(EXPECTED.read_text())
    if name not in expected:
        raise KeyError(f"unknown check {name!r}, known checks are {sorted(expected)}")
    entry = expected[name]
    try:
        got = run(name, fn)
    except NotImplementedError:
        if verbose:
            print(f"{name}  not implemented yet")
        return Result(False)
    except Exception as exc:  # report, do not crash the notebook
        if verbose:
            print(f"{name}  FAIL, your function raised {type(exc).__name__} ({exc})")
        return Result(False)
    for i, (case, g, e) in enumerate(zip(entry["cases"], got, entry["values"])):
        if not _close(g, e, entry.get("rtol", _RTOL)):
            if verbose:
                print(f"{name}  FAIL on case {i} {case}\n  expected {_short(e)}\n  got      {_short(g)}")
            return Result(False)
    if verbose:
        print(f"{name}  PASS ({len(got)} cases)")
    return Result(True)


# --- input cases for each task --------------------------------------------------
# Each adapter returns a list of results. CASES describes the inputs in messages.

CASES = {
    "lab0.gemm": [(197, 192, 576, 8), (64, 64, 64, 16), (1, 768, 192, 8), (197, 64, 197, 4)],
    "lab0.attention": [(64, 192, 3), (197, 192, 3), (1024, 192, 3), (128, 256, 8)],
    "lab0.breakdown": [197, 1024],
    "lab1.footprint": [(32, 64, 32, 8), (16, 192, 64, 8), (64, 64, 64, 16), (1, 1, 1, 4)],
    "lab1.traffic": [(197, 192, 576, 32, 192, 64, 8), (197, 192, 576, 64, 64, 64, 8),
                     (197, 768, 192, 197, 768, 16, 8), (197, 64, 197, 197, 64, 197, 8),
                     (100, 50, 30, 100, 16, 30, 16), (64, 64, 64, 16, 16, 64, 8)],
    "lab1.best": [(197, 192, 576), (197, 64, 197), (197, 197, 64), (197, 768, 192), (1024, 64, 1024)],
    "lab2.ws_tile": [(4, 4, 4), (197, 4, 4), (10, 3, 2), (1, 1, 1), (64, 16, 16), (197, 16, 9)],
    "lab2.ws_gemm": [(197, 64, 197, 4, 4), (197, 192, 576, 16, 16), (64, 64, 64, 8, 8),
                     (13, 7, 6, 4, 4), (197, 768, 192, 16, 16)],
    "lab3.lut_exp": [(-8.0, 0.0, 16), (-8.0, 0.0, 64), (-4.0, 0.0, 8)],
    "lab3.lut_gelu": [(-4.0, 4.0, 32), (-3.0, 3.0, 8)],
    "lab3.exp_shift": ["linspace(-10, 0, 41)"],
    "lab3.softmax": ["np.exp on 4x6 scores", "exp_ibert on 4x6 scores"],
    "lab4.pareto": ["12 fixed points", "duplicates and ties", "single point"],
}


@adapter("lab0.gemm")
def _(fn):
    return [list(fn(*c)) for c in CASES["lab0.gemm"]]


@adapter("lab0.attention")
def _(fn):
    return [fn(*c) for c in CASES["lab0.attention"]]


@adapter("lab0.breakdown")
def _(fn):
    from .workloads import vit_block
    out = []
    for seq in CASES["lab0.breakdown"]:
        res = fn(vit_block(seq=seq))
        out.append({k: [float(v[0]), float(v[1])] for k, v in sorted(res.items())})
    return out


@adapter("lab1.footprint")
def _(fn):
    return [fn(*c) for c in CASES["lab1.footprint"]]


@adapter("lab1.traffic")
def _(fn):
    return [fn(*c) for c in CASES["lab1.traffic"]]


@adapter("lab1.best")
def _(fn):
    out = []
    for c in CASES["lab1.best"]:
        traffic, tile = fn(*c, buffer_bytes=64 * 1024, bits=8)
        out.append(traffic)
    return out


@adapter("lab2.ws_tile")
def _(fn):
    return [fn(*c) for c in CASES["lab2.ws_tile"]]


@adapter("lab2.ws_gemm")
def _(fn):
    return [fn(*c) for c in CASES["lab2.ws_gemm"]]


def _gelu_ref(x):
    from .nonlinear import gelu
    return gelu(x)


@adapter("lab3.lut_exp")
def _(fn):
    x = np.linspace(-9, 0.5, 39)
    return [fn(np.exp, lo, hi, n)(x) for lo, hi, n in CASES["lab3.lut_exp"]]


@adapter("lab3.lut_gelu")
def _(fn):
    x = np.linspace(-3.5, 3.5, 29)
    return [fn(_gelu_ref, lo, hi, n)(x) for lo, hi, n in CASES["lab3.lut_gelu"]]


@adapter("lab3.exp_shift")
def _(fn):
    return [fn(np.linspace(-10, 0, 41))]


def _scores():
    return np.random.default_rng(42).normal(scale=2.0, size=(4, 6))


@adapter("lab3.softmax")
def _(fn):
    from .nonlinear import exp_ibert
    s = _scores()
    return [fn(s, np.exp), fn(s, exp_ibert)]


def _pareto_cases():
    rng = np.random.default_rng(7)
    pts = [tuple(p) for p in np.round(rng.uniform(0.2, 2.0, size=(12, 2)), 2)]
    ties = [(1.0, 5.0), (1.0, 5.0), (1.0, 4.0), (2.0, 4.0), (0.5, 9.0), (3.0, 1.0)]
    return [pts, ties, [(1.0, 1.0)]]


@adapter("lab4.pareto")
def _(fn):
    return [sorted(int(i) for i in fn(pts)) for pts in _pareto_cases()]

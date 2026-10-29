"""Softmax, GELU and LayerNorm: exact references, published approximations,
and an operation counter so that accuracy can be traded against cost.

The integer-friendly approximations follow I-BERT (Kim et al., ICML 2021):
second-order polynomials after a range reduction, so that exp and erf need
only multiplies, adds and shifts. They are written in floating point here for
readability; the operation counts are those of the integer version.
"""

from __future__ import annotations

from collections import Counter
import math

import numpy as np

from . import energy

LN2 = math.log(2.0)


class OpCounter:
    """Counts primitive operations: ``ops.add("mul", n)``."""

    def __init__(self):
        self.counts = Counter()

    def add(self, op: str, n: int = 1) -> None:
        self.counts[op] += int(n)

    def total(self) -> int:
        return sum(self.counts.values())

    def per_element(self, n_elements: int) -> dict:
        return {k: v / n_elements for k, v in sorted(self.counts.items())}

    def energy_pj(self, bits: int = 32) -> float:
        return energy.primitive_energy(self.counts, bits)

    def __repr__(self) -> str:
        return f"OpCounter({dict(sorted(self.counts.items()))})"


def _ops(ops):
    return ops if ops is not None else OpCounter()


# --- exact references ------------------------------------------------------

def softmax(x, axis: int = -1, ops: OpCounter | None = None):
    """Numerically stable softmax: exp(x - max) / sum."""
    ops = _ops(ops)
    x = np.asarray(x, float)
    z = x - x.max(axis=axis, keepdims=True)
    e = np.exp(z)
    out = e / e.sum(axis=axis, keepdims=True)
    n = x.size
    ops.add("cmp", n); ops.add("add", n); ops.add("exp", n); ops.add("add", n); ops.add("div", n)
    return out


_erf = np.vectorize(math.erf, otypes=[float])


def gelu(x, ops: OpCounter | None = None):
    """Exact GELU, x * Phi(x), using the error function."""
    ops = _ops(ops)
    x = np.asarray(x, float)
    ops.add("mul", 3 * x.size); ops.add("add", x.size); ops.add("exp", x.size)  # erf ~ exp cost
    return 0.5 * x * (1.0 + _erf(x / math.sqrt(2.0)))


def layernorm(x, gamma=1.0, beta=0.0, eps: float = 1e-5, ops: OpCounter | None = None):
    ops = _ops(ops)
    x = np.asarray(x, float)
    mu = x.mean(axis=-1, keepdims=True)
    var = ((x - mu) ** 2).mean(axis=-1, keepdims=True)
    n, rows = x.size, x.size // x.shape[-1]
    ops.add("add", 4 * n); ops.add("mul", 3 * n); ops.add("rsqrt", rows)
    return (x - mu) / np.sqrt(var + eps) * gamma + beta


# --- classic float approximations of GELU -----------------------------------

def gelu_tanh(x, ops: OpCounter | None = None):
    """Hendrycks and Gimpel's tanh form (used by BERT)."""
    ops = _ops(ops)
    x = np.asarray(x, float)
    ops.add("mul", 6 * x.size); ops.add("add", 2 * x.size); ops.add("tanh", x.size)
    return 0.5 * x * (1.0 + np.tanh(math.sqrt(2.0 / math.pi) * (x + 0.044715 * x ** 3)))


def gelu_sigmoid(x, ops: OpCounter | None = None):
    """x * sigmoid(1.702 x), from the same paper."""
    ops = _ops(ops)
    x = np.asarray(x, float)
    ops.add("mul", 2 * x.size); ops.add("add", x.size); ops.add("exp", x.size); ops.add("div", x.size)
    return x / (1.0 + np.exp(-1.702 * x))


# --- I-BERT polynomial approximations -------------------------------------

def exp_ibert(x, ops: OpCounter | None = None):
    """exp(x) for x <= 0: x = -z ln2 + p, exp(p) ~ 0.3585 (p + 1.353)^2 + 0.344,
    then a right shift by z."""
    ops = _ops(ops)
    x = np.minimum(np.asarray(x, float), 0.0)
    z = np.floor(-x / LN2)
    p = x + z * LN2
    poly = 0.3585 * (p + 1.353) ** 2 + 0.344
    n = x.size
    ops.add("mul", 3 * n); ops.add("floor", n); ops.add("add", 3 * n); ops.add("shift", n)
    return poly * 2.0 ** (-z)


def softmax_ibert(x, axis: int = -1, ops: OpCounter | None = None):
    ops = _ops(ops)
    x = np.asarray(x, float)
    z = x - x.max(axis=axis, keepdims=True)
    e = exp_ibert(z, ops)
    s = e.sum(axis=axis, keepdims=True)
    n, rows = x.size, x.size // x.shape[axis]
    # one reciprocal per row, then a multiply per element
    ops.add("cmp", n); ops.add("add", 2 * n); ops.add("div", rows); ops.add("mul", n)
    return e / s


def gelu_ibert(x, ops: OpCounter | None = None):
    """GELU with erf(x) ~ sign(x) [a (min(|x|, -b) + b)^2 + 1], a=-0.2888, b=-1.769."""
    ops = _ops(ops)
    x = np.asarray(x, float)
    a, b = -0.2888, -1.769
    u = np.abs(x / math.sqrt(2.0))
    erf = np.sign(x) * (a * (np.minimum(u, -b) + b) ** 2 + 1.0)
    n = x.size
    ops.add("mul", 5 * n); ops.add("add", 3 * n); ops.add("cmp", 2 * n)
    return 0.5 * x * (1.0 + erf)


# --- using them --------------------------------------------------------------

def attention(Q, K, V, softmax_fn=softmax, ops: OpCounter | None = None):
    """Single-head scaled dot-product attention with a pluggable softmax."""
    Q, K, V = (np.asarray(t, float) for t in (Q, K, V))
    scores = Q @ K.T / math.sqrt(Q.shape[-1])
    P = softmax_fn(scores, ops=ops) if ops is not None else softmax_fn(scores)
    return P @ V


def error_stats(approx, exact) -> dict:
    approx, exact = np.asarray(approx, float), np.asarray(exact, float)
    err = np.abs(approx - exact)
    return dict(max_abs=float(err.max()), mean_abs=float(err.mean()),
                max_rel=float((err / np.maximum(np.abs(exact), 1e-12)).max()))

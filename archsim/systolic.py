"""Cycle-level simulation of a rows x cols systolic MAC array.

Two dataflows (terminology from Chen, Emer and Sze, ISCA 2016 / Sze et al. 2017):

* Output-stationary (OS). Each PE owns one output C[i, j]. Rows of A enter
  from the left, columns of B from the top, both skewed by one cycle per row
  or column. A tile covers up to rows x cols outputs and streams all of K.
* Weight-stationary (WS). Each PE holds one weight W[k, j], loaded before
  compute. Rows of A enter from the left (skewed), partial sums flow down and
  leave at the bottom. A tile covers up to rows x cols weights and streams all
  M input rows.

The tile simulators move real values, so the result can be checked against
``A @ B``. A full GEMM is a sequence of tiles. We assume tiles do not overlap
(no double buffering), which keeps the cycle counts easy to reason about.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
import math

import numpy as np


@dataclass
class TileResult:
    out: np.ndarray
    cycles: int
    macs: int
    load_cycles: int = 0
    frames: list = field(default_factory=list)  # per-cycle snapshots if trace=True

    def utilization(self, rows: int, cols: int) -> float:
        return self.macs / (self.cycles * rows * cols)


def _skew(X: np.ndarray, lanes: int, steps: int) -> tuple[np.ndarray, np.ndarray]:
    """Stream for ``lanes`` input ports, where lane i sees X[i, t - i] at cycle t."""
    vals = np.zeros((lanes, steps))
    valid = np.zeros((lanes, steps), dtype=bool)
    for i in range(min(lanes, X.shape[0])):
        n = X.shape[1]
        vals[i, i:i + n] = X[i]
        valid[i, i:i + n] = True
    return vals, valid


def simulate_os_tile(A, B, rows: int = 4, cols: int = 4, trace: bool = False) -> TileResult:
    """Output-stationary tile. A is (m x K) with m <= rows, B is (K x n) with n <= cols."""
    A, B = np.asarray(A, float), np.asarray(B, float)
    m, K = A.shape
    n = B.shape[1]
    assert m <= rows and n <= cols and B.shape[0] == K
    steps = K + rows + cols
    a_in, a_ok = _skew(A, rows, steps)
    b_in, b_ok = _skew(B.T, cols, steps)

    a = np.zeros((rows, cols))
    va = np.zeros((rows, cols), bool)
    b = np.zeros((rows, cols))
    vb = np.zeros((rows, cols), bool)
    acc = np.zeros((rows, cols))
    frames, macs, last = [], 0, -1
    for t in range(steps):
        a[:, 1:], va[:, 1:] = a[:, :-1].copy(), va[:, :-1].copy()   # A moves right
        b[1:, :], vb[1:, :] = b[:-1, :].copy(), vb[:-1, :].copy()   # B moves down
        a[:, 0], va[:, 0] = a_in[:, t], a_ok[:, t]
        b[0, :], vb[0, :] = b_in[:, t], b_ok[:, t]
        active = va & vb
        acc[active] += a[active] * b[active]
        if active.any():
            macs += int(active.sum())
            last = t
        if trace:
            frames.append(dict(a=np.where(va, a, np.nan), b=np.where(vb, b, np.nan),
                               acc=acc.copy(), active=active.copy()))
    return TileResult(acc[:m, :n], cycles=last + 1, macs=macs, frames=frames[:last + 1])


def simulate_ws_tile(A, W, rows: int = 4, cols: int = 4, trace: bool = False) -> TileResult:
    """Weight-stationary tile. W is (k x n) with k <= rows and n <= cols, A is (M x k).

    Loading W takes one cycle per array row used (weights shift in from the top).
    """
    A, W = np.asarray(A, float), np.asarray(W, float)
    M, k = A.shape
    n = W.shape[1]
    assert k <= rows and n <= cols and W.shape[0] == k
    load = k
    w = np.zeros((rows, cols))
    w[:k, :n] = W
    steps = M + rows + cols
    x_in, x_ok = _skew(A.T, rows, steps)           # row r of the array gets column r of A
    tok_in = np.full((rows, steps), -1)
    for r in range(k):
        tok_in[r, r:r + M] = np.arange(M)

    x = np.zeros((rows, cols))
    vx = np.zeros((rows, cols), bool)
    tok = np.full((rows, cols), -1)
    psum = np.zeros((rows, cols))
    out = np.zeros((M, n))
    frames, macs, last = [], 0, -1
    if trace:                              # weights enter at the top and shift down one row per cycle
        for i in range(load):
            wv = np.full((rows, cols), np.nan)
            wv[:i + 1, :n] = W[k - 1 - i:, :]
            frames.append(dict(x=np.full((rows, cols), np.nan), w=wv, psum=np.zeros((rows, cols)),
                               active=np.zeros((rows, cols), bool), phase="loading weights"))
    for t in range(steps):
        x[:, 1:], vx[:, 1:], tok[:, 1:] = x[:, :-1].copy(), vx[:, :-1].copy(), tok[:, :-1].copy()
        x[:, 0], vx[:, 0], tok[:, 0] = x_in[:, t], x_ok[:, t], tok_in[:, t]
        active = vx & (np.arange(cols) < n)[None, :]
        above = np.vstack([np.zeros((1, cols)), psum[:-1]])     # psums move down
        psum = above + np.where(active, x * w, 0.0)
        psum[k:] = 0.0                     # results leave at row k-1, unused rows are bypassed
        if active.any():
            macs += int(active.sum())
            last = t
        done = active[k - 1]                                   # bottom used row emits
        out[tok[k - 1, done], np.nonzero(done)[0]] = psum[k - 1, done]
        if trace:
            frames.append(dict(x=np.where(vx, x, np.nan), w=w.copy(),
                               psum=psum.copy(), active=active.copy()))
    return TileResult(out, cycles=load + last + 1, macs=macs, load_cycles=load,
                      frames=frames[:load + last + 1] if trace else [])


def os_tile_cycles(m: int, k: int, n: int) -> int:
    """Closed form of simulate_os_tile's cycle count (checked in the unit tests)."""
    return k + m + n - 2


@lru_cache(maxsize=4096)
def _ws_tile_cycles_sim(m: int, k: int, n: int, rows: int, cols: int) -> int:
    return simulate_ws_tile(np.ones((m, k)), np.ones((k, n)), rows, cols).cycles


def _tiles(size: int, step: int) -> list[int]:
    return [min(step, size - s) for s in range(0, size, step)]


def gemm(M: int, K: int, N: int, rows: int = 4, cols: int = 4, dataflow: str = "os") -> dict:
    """Cycles and utilization of an (M x K) @ (K x N) GEMM, tile by tile."""
    cycles, tiles = 0, 0
    if dataflow == "os":
        for m in _tiles(M, rows):
            for n in _tiles(N, cols):
                cycles += os_tile_cycles(m, K, n)
                tiles += 1
    elif dataflow == "ws":
        for k in _tiles(K, rows):
            for n in _tiles(N, cols):
                cycles += _ws_tile_cycles_sim(M, k, n, rows, cols)
                tiles += 1
    else:
        raise ValueError("dataflow must be 'os' or 'ws'")
    return dict(cycles=cycles, tiles=tiles, macs=M * K * N,
                utilization=M * K * N / (cycles * rows * cols))


def matmul(A, B, rows: int = 4, cols: int = 4, dataflow: str = "os") -> tuple[np.ndarray, int]:
    """Compute A @ B by running every tile through the simulator. Returns (C, cycles)."""
    A, B = np.asarray(A, float), np.asarray(B, float)
    M, K = A.shape
    N = B.shape[1]
    C = np.zeros((M, N))
    cycles = 0
    if dataflow == "os":
        for i in range(0, M, rows):
            for j in range(0, N, cols):
                r = simulate_os_tile(A[i:i + rows], B[:, j:j + cols], rows, cols)
                C[i:i + rows, j:j + cols] = r.out
                cycles += r.cycles
    else:
        for p in range(0, K, rows):
            for j in range(0, N, cols):
                r = simulate_ws_tile(A[:, p:p + rows], B[p:p + rows, j:j + cols], rows, cols)
                C[:, j:j + cols] += r.out      # partial sums over K tiles
                cycles += r.cycles
    return C, cycles


def ideal_cycles(M: int, K: int, N: int, rows: int, cols: int) -> int:
    """Lower bound, with every PE busy every cycle."""
    return math.ceil(M * K * N / (rows * cols))

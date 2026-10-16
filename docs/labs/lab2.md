# Lab 2: Systolic arrays

**30 minutes.** [Open in the browser](https://rht0111.github.io/edge-ai-arch-lab/lite/lab/index.html?path=lab2_systolic.ipynb){ .md-button }
[Open in Colab](https://colab.research.google.com/github/rht0111/edge-ai-arch-lab/blob/master/labs/lab2_systolic.ipynb){ .md-button }

## Goals

* Watch a 4 x 4 output-stationary array compute a GEMM, cycle by cycle.
* Measure utilization on shapes that do not match the array, such as 197 tokens.
* Derive a cycle model for weight-stationary from the simulator and compare the two dataflows.

## Background

A systolic array (Kung, 1982) is a grid of processing elements (PEs) that
pass operands to their neighbours every cycle, so that each value fetched from
the buffer is used by a whole row or column of PEs. The TPU (Jouppi et al.,
2017) made the idea famous for neural networks.

The *dataflow* says which operand stays in a PE (Chen, Emer and Sze, 2016;
Sze et al., 2017):

* **Output-stationary (OS).** PE (i, j) accumulates C[i, j]. Row i of A
  enters from the left delayed by i cycles, column j of B from the top delayed
  by j cycles. A tile of m x n outputs with reduction length K takes
  K + m + n − 2 cycles.
* **Weight-stationary (WS).** PE (k, j) holds W[k, j], loaded before compute.
  Activations stream from the left, partial sums flow down. A tile covers up to
  rows x cols weights and streams every row of A through them.

`archsim.systolic` moves real values through the array, so its results are
checked against `A @ B`. Tiles run one after the other (no overlap of one
tile's drain with the next tile's fill), which keeps the counts easy to reason
about and makes the overheads visible.

Two things keep utilization below 100%:

* **Shape mismatch.** 197 tokens on a 16-row array leave the last tile with
  5 useful rows out of 16.
* **Fill and drain.** With OS, each tile pays rows + cols − 2 cycles of skew; if
  K is short (64 for an attention head) that is a large fraction.

## Tasks

1. From simulator runs, find the closed form of `ws_tile_cycles(m, k, n)`.
2. `ws_gemm_cycles(M, K, N, rows, cols)`: tile the GEMM and add up.
3. Compare OS and WS on every GEMM of the block, for 4 x 4 and 16 x 16 arrays.

## What you should see

Small arrays are easy to keep busy. On 16 x 16 the per-head QKᵀ of ViT-Tiny
reaches only about 60% utilization in OS and below 80% in WS; peak TOPS
overstates what this workload gets by a large factor.

## Reflection

Give the utilization of the `scores` GEMM on a 16 x 16 array for both
dataflows, and say what would have to change in the workload or the array to
reach 90%.

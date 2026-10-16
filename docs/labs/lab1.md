# Lab 1: Roofline and tiling

**25 minutes.** [Open in the browser](https://rht0111.github.io/edge-ai-arch-lab/lite/lab/index.html?path=lab1_roofline_tiling.ipynb){ .md-button }
[Open in Colab](https://colab.research.google.com/github/rht0111/edge-ai-arch-lab/blob/master/labs/lab1_roofline_tiling.ipynb){ .md-button }

## Goals

* Place the operators of a ViT-Tiny block on the roofline of a toy edge accelerator.
* Choose GEMM tile sizes that minimise DRAM traffic under a 64 KiB buffer.
* Decide when the attention GEMMs are memory-bound.

## The machine

| | |
|---|---|
| MAC array | 16 x 16 at 50 MHz, 25.6 GOP/s peak (1 MAC = 2 ops) |
| DRAM link | 0.4 GB/s |
| Ridge point | 64 ops/byte |
| On-chip buffer | 64 KiB |

## Background

The roofline model (Williams, Waterman and Patterson, 2009) bounds the
attainable performance of a kernel by min(peak, bandwidth × intensity). Left
of the ridge point a kernel is memory-bound: faster arithmetic does not help.

The intensity of Lab 0 assumed each tensor crosses the DRAM link once. With a
finite buffer, a GEMM is computed in tiles and some operands are fetched
several times. The lab uses one loop nest, output-stationary at the buffer
level: the C tile stays on chip while K is traversed, and an A or B tile is
reloaded whenever the next iteration needs a different one. Under that rule

* A is read once if all of K fits in one tile (it then only changes with the
  M index), otherwise once per column of C tiles;
* B is read once only if both K and N fit in one tile, otherwise once per row
  of C tiles;
* C is written once.

The footprint counts one A tile and one B tile at the data precision, and one
C tile of 32-bit accumulators.

Two remarks for the discussion:

* Tiny output tiles minimise the footprint but starve the MAC array; the lab
  requires Tm, Tn ≥ 16 to match the 16x16 array.
* Each crossing of the DRAM link costs about 160 pJ per byte in the
  illustrative table, 500 times an int8 MAC. Reuse decides energy, not just speed.

## Tasks

1. `footprint(Tm, Tk, Tn, bits)`: bytes of buffer used by one set of tiles.
2. `tiled_traffic(M, K, N, Tm, Tk, Tn, bits)`: DRAM bytes of the loop nest.
3. `best_tiling(M, K, N, buffer_bytes, bits)`: exhaustive search over power-of-two tiles.

## What you should see

At 197 tokens most GEMMs reach the minimum traffic with 64 KiB; the MLP's
second layer, whose 768-wide input cannot stay on chip, does not. Shrink the
buffer to 16 KiB and every GEMM falls below the ridge. The per-head QKᵀ is
memory-bound at 64 tokens whatever the buffer, and at 197 tokens only with a
small buffer. Even at the minimum, the DRAM energy of the block is several
times its MAC energy.

## Stretch

Double buffering, attention fusion (the idea behind FlashAttention, Dao et
al., 2022) and a weight-stationary loop order.

## Reflection

Which property of a GEMM's shape decides how much a small buffer hurts, and
what does that imply for how much SRAM area a 1 mW chip should spend?

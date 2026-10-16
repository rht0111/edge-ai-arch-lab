# Lab 0: Profile a Transformer block

**15 minutes.** [Open in the browser](https://rht0111.github.io/edge-ai-arch-lab/lite/lab/index.html?path=lab0_profile.ipynb){ .md-button }
[Open in Colab](https://colab.research.google.com/github/rht0111/edge-ai-arch-lab/blob/main/labs/lab0_profile.ipynb){ .md-button }

## Goals

* Count the operations and bytes of each operator of one ViT-Tiny encoder block.
* See how the breakdown moves between 64 and 1024 tokens.
* See that the operators with the fewest FLOPs are not the cheapest.

## Background

A pre-norm encoder block is LayerNorm, a QKV projection, per-head attention
(QKᵀ, softmax, PV), an output projection, a residual add, a second LayerNorm,
a two-layer MLP with GELU and a second residual add. With sequence length *S*
and embedding size *D* the GEMMs perform

* 4·S·D² MACs for the QKV and output projections,
* 2·S²·D MACs for the two attention GEMMs (independent of the number of heads),
* 8·S·D² MACs for the MLP with hidden size 4·D.

Attention grows with S², everything else with S. The two are equal when
S = 4·D, i.e. 768 tokens for ViT-Tiny.

Arithmetic intensity, operations per byte moved, is the quantity that decides
whether a piece of hardware waits for data or for arithmetic (Lab 1). A GEMM
with many tokens reuses each weight many times and has high intensity; the
same weights applied to one token (a matrix-vector product) have intensity
about 2 when weights are 8-bit.

## Tasks

1. `gemm_flops_bytes(M, K, N, bits)`: operations and minimum bytes of a GEMM.
2. `attention_flops(seq, dim, heads)`: operations of QKᵀ and PV over all heads.
3. `cost_breakdown(ops)`: FLOPs and compute energy per operator kind, using
   int8 MACs for GEMMs and FP32 software for everything else.

## What you should see

GEMMs are about 98% of the FLOPs. With the illustrative energy table, softmax
and GELU, under 2% of the FLOPs, account for roughly a third of the
*compute* energy at 197 tokens, because one FP32 `exp` costs as much as about a
hundred int8 MACs. Data movement is not even counted yet.

## Reflection

Which of your numbers support each of the three lecture claims: GEMM
dominates compute; attention scales with sequence length; non-linear
functions are small in FLOPs, not in cost?

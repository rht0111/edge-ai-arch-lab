# Lab 3. Non-linear functions in hardware

**25 minutes.** [Open in the browser](https://rht0111.github.io/edge-ai-arch-lab/lite/lab/index.html?path=lab3_nonlinear.ipynb){ .md-button }
[Open in Colab](https://colab.research.google.com/github/rht0111/edge-ai-arch-lab/blob/students/labs/lab3_nonlinear.ipynb){ .md-button }

## Goals

* Implement softmax and GELU three ways, as a floating-point reference, a
  lookup table, and an integer-friendly approximation.
* Plot accuracy against cost per element.
* Use your softmax inside an attention head and judge whether it is good enough.

## Background

A MAC array computes sums of products. Softmax needs `exp` and a division,
GELU needs `erf` (or `tanh`), and LayerNorm needs a reciprocal square root.
On a general-purpose core these cost tens of operations each. An accelerator
has three options.

* **Lookup table.** Cheap and simple, with an accuracy set by the number of
  entries and the input range. A piecewise-constant table is crude near the
  maximum of softmax, where most of the probability mass is.
* **Shift-based exponential.** exp(x) = 2^(x·log₂e). Split the exponent into
  an integer part, which is a shift, and a fraction f, approximated by 1 + f.
  The relative error is at most about 6%.
* **Polynomial after range reduction.** I-BERT (Kim et al., 2021) computes
  exp with a second-order polynomial on a reduced interval and a shift, and
  erf with a clipped second-order polynomial, all in integer arithmetic.

Whether an approximation is acceptable is not a property of the function. It
depends on what consumes it, so the lab measures the error of the attention
output and not only of the probabilities.

## Tasks

1. `make_lut(f, lo, hi, n)` builds a table of `f` at bin centres, indexed with clamping.
2. `exp_shift(x)` is the shift-based exponential.
3. `softmax_approx(x, exp_fn)` is a softmax with a pluggable exponential.

## Stretch

Map the shift-based exponential onto the toy 4 x 4 CGRA of `archsim.cgra`
and compare its energy per element with a fixed-function unit. Coarse-grained
reconfigurable arrays trade some energy for the ability to run several such
kernels on the same silicon (see [Going further](../going-further.md)).

## Reflection

Pick one exponential for the 1 mW chip and justify it. What accuracy did you
require, and where did that requirement come from?

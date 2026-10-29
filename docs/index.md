# Edge AI Architecture Lab

Hands-on session of the invited lecture *How Transformers reshape computer
architecture*, Sorbonne Université, "Hot Topics" series, session 9, on
Tuesday 8 December 2026 from 13:45 to 18:00.

[Launch the labs in your browser](https://rht0111.github.io/edge-ai-arch-lab/lite/lab/index.html?path=lab0_profile.ipynb){ .md-button .md-button--primary }
[Setup and other ways to run](setup.md){ .md-button }

## The scenario

You are the architect of a ~1 mW edge chip that must run a ViT-Tiny image
classifier (12 Transformer encoder blocks, 197 tokens, embedding size 192).
Where do the cycles and the energy go, and what would you build?

Over two hours, with a lab partner, you build the answer from small pieces.
You count the work, see how much data has to move, watch a systolic array
run, make `exp` cheap, and finally commit to a design under an area budget.
Every lab ends with a number you can compare with the rest of the class, and
the session ends with the class Pareto plot on the projector.

## Schedule

| Time | Part | |
|---|---|---|
| 13:45 | Lecture (slides) | Transformers, GEMM, memory movement, irregular workloads, non-linear operations, programmability |
| 15:45 | Break | |
| 16:00 | [Lab 0. Profile a Transformer](labs/lab0.md) | 15 min |
| 16:15 | [Lab 1. Roofline and tiling](labs/lab1.md) | 25 min |
| 16:40 | [Lab 2. Systolic arrays](labs/lab2.md) | 30 min |
| 17:10 | [Lab 3. Non-linear functions in hardware](labs/lab3.md) | 25 min |
| 17:35 | [Lab 4. Design challenge](labs/lab4.md) | 25 min, class Pareto plot at the end |

If you fall behind, skip the stretch tasks. Each lab stands on its own, and
Lab 4 only needs the `archsim` package, not your earlier answers.

## How each lab works

Every notebook has the same shape.

* Goals and a short background (the long version is on this site).
* Tasks marked `# TODO`, each followed by a `check(...)` cell that tells you
  at once whether your function is right.
* One or two stretch tasks.
* A reflection question that links back to the lecture.

The models live in a small Python package, `archsim`, written to be read.
Its numbers are **illustrative** (45 nm, from published tables plus stated
assumptions). They are good for comparing designs with each other, not for
predicting a real chip, and part of the exercise is to say where they are wrong.

## Three ways to run

1. **In the browser, with nothing to install** (recommended). The button above
   opens JupyterLite. Python runs inside your browser tab and your files stay
   in the browser's storage, so download anything you want to keep.
2. **Google Colab.** Every notebook has an *Open in Colab* badge.
3. **On your own computer.** Run `pip install -e ".[lab]"` in a clone of the
   repository, then `jupyter lab`. See [Setup](setup.md).

## Source and licence

Code, notebooks and this site are on
[GitHub](https://github.com/rht0111/edge-ai-arch-lab). Code is under the MIT
licence, and text and figures are under CC BY 4.0.

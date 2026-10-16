# Edge AI Architecture Lab

Hands-on lab for the invited lecture *How Transformers reshape computer
architecture* (Sorbonne Université, "Hot Topics" series, session 9,
Tuesday 8 December 2026, 13:45 to 18:00).

**Course site:** https://rht0111.github.io/edge-ai-arch-lab/

**Launch in the browser (no install):**
https://rht0111.github.io/edge-ai-arch-lab/lite/lab/index.html?path=lab0_profile.ipynb

The lecture covers why GEMM dominates Transformer compute, why memory movement
and non-linear operations matter more than their FLOPs suggest, and the
trade-offs among performance, energy, area, flexibility and HW/SW co-design.
The lab makes each point measurable with one running scenario:

> You are the architect of a ~1 mW edge chip that must run a ViT-Tiny
> Transformer. Where do the cycles and the energy go, and what would you build?

## Labs

Two hours, in pairs. Each notebook has goals, a short background, `# TODO`
tasks with an instant `check(...)`, stretch tasks and a reflection question.

| Notebook | Time | You build | Takeaway |
|---|---|---|---|
| [Lab 0: Profile a Transformer](labs/lab0_profile.ipynb) | 15 min | FLOP and byte counts of a ViT-Tiny block, at 64 and 1024 tokens | GEMM dominates compute; attention grows with the sequence; non-linear ops are small in FLOPs, not in cost |
| [Lab 1: Roofline and tiling](labs/lab1_roofline_tiling.ipynb) | 25 min | A tiling search under a 64 KiB buffer; the block on a roofline | Data reuse sets energy |
| [Lab 2: Systolic arrays](labs/lab2_systolic.ipynb) | 30 min | An animated 4x4 output-stationary array; a weight-stationary cycle model | Dataflow and shape mismatch decide real efficiency, not peak TOPS |
| [Lab 3: Non-linear functions](labs/lab3_nonlinear.ipynb) | 25 min | Softmax and GELU as float, LUT and shift-based approximations | Non-linear functions are a hardware design problem |
| [Lab 4: Design challenge](labs/lab4_design_challenge.ipynb) | 25 min | A chip under an area budget, exported as `submission.json` | Pareto trade-offs |

## Three ways to run

**A. In the browser (recommended).** Open the launch link above. JupyterLite
runs Python in the browser tab; nothing is installed. Download your files
before closing the tab if you want to keep them.

**B. Google Colab.** Each notebook has an *Open in Colab* badge.

**C. Locally** (Python 3.10 or newer):

```bash
git clone https://github.com/rht0111/edge-ai-arch-lab.git
cd edge-ai-arch-lab
pip install -e ".[lab]"      # or: uv sync --extra lab
jupyter lab labs/
```

Check your answers from a terminal with `pytest tests/test_lab1.py`
(after `pip install -e ".[dev]"`). See the
[setup page](https://rht0111.github.io/edge-ai-arch-lab/setup/) for
troubleshooting on university PCs.

## Repository layout

```
archsim/       small Python package used by the notebooks (numpy + matplotlib)
  workloads.py   Transformer block as a list of operators: shapes, FLOPs, bytes
  energy.py      45 nm energy and area per operation and per access (illustrative)
  roofline.py    roofline model and the toy edge accelerator
  systolic.py    cycle-level output- and weight-stationary array simulator
  nonlinear.py   exact and approximate softmax, GELU, LayerNorm with op counters
  cgra.py        toy 4x4 CGRA mapper
  design.py      design-space model: latency, energy, area of a whole chip
  checks.py      the check() used in the notebooks
labs/          the five notebooks
tests/         unit tests of archsim (tests/unit) and the lab checks (test_labN.py)
docs/          course site (MkDocs Material)
scripts/       collect_pareto.py: class Pareto plot from a folder of submissions
```

All numbers in `archsim` are illustrative and meant for comparing designs
with each other. Their sources and assumptions are listed in
[docs/references.md](docs/references.md).

## For instructors

Collect the `submission.json` files in one folder and run

```bash
python scripts/collect_pareto.py submissions/ -o class_pareto.png --show
```

Metrics are recomputed from each submitted design.

## Licence

Code: MIT ([LICENSE](LICENSE)). Text, notebooks' prose and figures:
CC BY 4.0 ([LICENSE-docs](LICENSE-docs)).

Rohit Prasad, CEA-List, Université Paris-Saclay.

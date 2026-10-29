# Lab 4. Design challenge

**25 minutes.** [Open in the browser](https://rht0111.github.io/edge-ai-arch-lab/lite/lab/index.html?path=lab4_design_challenge.ipynb){ .md-button }
[Open in Colab](https://colab.research.google.com/github/rht0111/edge-ai-arch-lab/blob/students/labs/lab4_design_challenge.ipynb){ .md-button }

## The challenge

Choose the MAC array size, the buffer size, the precision and the number of
lanes of optional softmax and GELU units. Stay within **1.0 mm²** (45 nm,
illustrative). The lowest energy per ViT-Tiny inference wins, and latency
breaks ties. Also report the frame rate your chip sustains at an average
power of 1 mW.

## The model

`archsim.design.evaluate` combines the previous labs.

* GEMM cycles come from the output-stationary systolic model of Lab 2.
* DRAM traffic comes from a simple tiling heuristic, with a lower bound set by
  the weights, which are streamed once per inference (5.3 MB of int8 weights
  do not fit on this chip).
* Softmax and GELU run on their units if present, otherwise on a 4-lane host
  core at FP32 software cost (Lab 3). LayerNorm and residual adds always run
  on the host.
* Energy and area come from the illustrative 45 nm table, plus stated
  assumptions for SRAM area, leakage and the host core.

All of this is in the module docstring and in about 200 lines of code. You are
encouraged to disagree with it in your reflection.

## Steps

1. Read the baseline breakdowns. What dominates energy, latency and area?
2. Implement `pareto_front(points)`.
3. Sweep a grid of designs and look at the energy-area plane.
4. Choose your design, check it is within budget, and export `submission.json`.

## Collecting the class results

Each team downloads its `submission.json` (in JupyterLite, right-click it and
choose *Download*) and hands it in. The instructor collects the files in one
folder and runs the command below. The script recomputes every metric from the
submitted design, ranks the designs that meet the budget and draws the class
Pareto plot.

```bash
python scripts/collect_pareto.py submissions/ --show
```

## Reflection

Which decision mattered most for energy, and which for latency? Which of the
lecture's trade-offs (performance, energy, area, flexibility, HW/SW
co-design) did you give up, and why was that acceptable here?

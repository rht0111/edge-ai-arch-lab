"""Draw the class Pareto plot from a folder of Lab 4 submissions.

    python scripts/collect_pareto.py submissions/            # writes submissions/class_pareto.png

Every metric is recomputed from the design in each file, so edited numbers in
a submission have no effect. Files that do not parse are reported and skipped.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt

from archsim import design


def non_dominated(points):
    return [i for i, (a, e) in enumerate(points)
            if not any(a2 <= a and e2 <= e and (a2 < a or e2 < e) for a2, e2 in points)]


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("folder", type=Path)
    p.add_argument("-o", "--output", help="image file (default: FOLDER/class_pareto.png)")
    p.add_argument("--show", action="store_true", help="open a window (for the projector)")
    args = p.parse_args()
    args.output = args.output or str(args.folder / "class_pareto.png")
    if not args.show:
        matplotlib.use("Agg")

    subs = []
    for f in sorted(args.folder.glob("*.json")):
        try:
            subs.append(design.load_submission(f))
        except Exception as exc:
            print(f"skipping {f.name}: {type(exc).__name__}: {exc}")
    if not subs:
        raise SystemExit(f"no valid submissions in {args.folder}")

    ok = [s for s in subs if s["metrics"]["within_budget"]]
    ranked = sorted(ok, key=lambda s: (s["metrics"]["energy_uj"], s["metrics"]["latency_ms"]))
    print(f"{'rank':<5}{'team':<24}{'energy uJ':>10}{'latency ms':>12}{'area mm2':>10}{'fps@1mW':>9}  design")
    for i, s in enumerate(ranked, 1):
        m, d = s["metrics"], s["design"]
        print(f"{i:<5}{s['team'][:23]:<24}{m['energy_uj']:>10.0f}{m['latency_ms']:>12.0f}"
              f"{m['area_mm2']:>10.3f}{m['fps_at_1mw']:>9.3f}  {d}")
    for s in subs:
        if not s["metrics"]["within_budget"]:
            print(f"over budget: {s['team']} ({s['metrics']['area_mm2']:.3f} mm2)")

    pts = [(s["metrics"]["area_mm2"], s["metrics"]["energy_uj"]) for s in ok]
    front = sorted(non_dominated(pts), key=lambda i: pts[i][0])
    fig, ax = plt.subplots(figsize=(9, 6))
    for s in subs:
        m = s["metrics"]
        good = m["within_budget"]
        ax.plot(m["area_mm2"], m["energy_uj"], "o", ms=8,
                color="tab:blue" if good else "0.7", alpha=0.9)
        ax.annotate(f"{s['team']}: {m['energy_uj']:.0f} uJ, {m['latency_ms']:.0f} ms, {m['area_mm2']:.2f} mm2",
                    (m["area_mm2"], m["energy_uj"]), xytext=(5, 4),
                    textcoords="offset points", fontsize=9, color="black" if good else "0.5")
    if front:
        ax.plot([pts[i][0] for i in front], [pts[i][1] for i in front], "r-", lw=1.5, label="class Pareto front")
    ax.axvline(design.AREA_BUDGET_MM2, color="k", ls=":", label="area budget")
    ax.set_yscale("log")
    ax.set_xlabel("area (mm2, 45 nm, illustrative)")
    ax.set_ylabel("energy per ViT-Tiny inference (uJ)")
    ax.set_title(f"{len(subs)} submissions")
    ax.legend()
    fig.tight_layout()
    fig.savefig(args.output, dpi=150)
    print("wrote", args.output)
    if args.show:
        plt.show()


if __name__ == "__main__":
    main()

"""Regenerate archsim/data/expected.json from the reference notebooks.

Run on the solutions branch, where labs/ holds the solved notebooks:
    python scripts/make_expected.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tests"))

from archsim import checks  # noqa: E402
from nbtasks import TASKS, load  # noqa: E402


def main() -> None:
    out = {}
    for task, (notebook, name) in TASKS.items():
        fn = load(notebook)[name]
        out[task] = {"cases": [str(c) for c in checks.CASES[task]],
                     "values": checks.run(task, fn), "rtol": 1e-6}
    checks.EXPECTED.write_text(json.dumps(out, indent=1) + "\n")
    print(f"wrote {checks.EXPECTED} ({len(out)} checks)")


if __name__ == "__main__":
    main()

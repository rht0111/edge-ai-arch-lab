"""Regenerate archsim/data/expected.json from the reference notebooks.

Run it where labs/ holds the solved notebooks (master or solutions).

    python scripts/make_expected.py           # rewrite the file
    python scripts/make_expected.py --check   # only compare, within tolerance

CI uses --check, because the last digit of a float can differ between numpy
builds and a byte-for-byte comparison of the JSON would fail for no reason.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tests"))

from archsim import checks
from nbtasks import TASKS, load


def compute() -> dict:
    out = {}
    for task, (notebook, name) in TASKS.items():
        fn = load(notebook)[name]
        out[task] = {"cases": [str(c) for c in checks.CASES[task]],
                     "values": checks.run(task, fn), "rtol": 1e-6}
    return out


def main() -> None:
    out = compute()
    if "--check" not in sys.argv:
        checks.EXPECTED.write_text(json.dumps(out, indent=1) + "\n")
        print(f"wrote {checks.EXPECTED} ({len(out)} checks)")
        return
    stored = json.loads(checks.EXPECTED.read_text())
    stale = sorted(set(out) ^ set(stored))
    stale += [t for t in out if t in stored and (
        out[t]["cases"] != stored[t]["cases"]
        or not checks._close(out[t]["values"], stored[t]["values"], 1e-9))]
    if stale:
        sys.exit(f"expected.json is out of date for {', '.join(stale)}. Run scripts/make_expected.py")
    print(f"expected.json matches the solutions ({len(out)} checks)")


if __name__ == "__main__":
    main()

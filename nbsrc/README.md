# Notebook sources (solutions branch only)

Each `labN_*.txt` is one notebook with the reference solutions inside
`### BEGIN SOLUTION` / `### END SOLUTION` markers; the format is described in
`scripts/build_notebooks.py`. This branch is never merged into `master`.

To change a lab:

1. Edit the source here.
2. `python scripts/build_notebooks.py --solutions` and commit `labs/` on this branch.
3. If a task or its inputs changed: `python scripts/make_expected.py`
   (writes `archsim/data/expected.json`).
4. `python scripts/build_notebooks.py --stubs --out /tmp/stubs`, copy the stub
   notebooks (and `expected.json` if it changed) to `master`, commit there, then
   merge `master` back into this branch.

CI on this branch checks that `expected.json` matches the solutions, runs
`pytest tests` and executes every notebook.

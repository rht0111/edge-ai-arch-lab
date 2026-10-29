# Instructor notes (master and solutions only)

## Branches

| Branch | Contents | Who sees it |
|---|---|---|
| `master` | everything: package, solved notebooks, notebook sources, scripts | instructor |
| `solutions` | same as `master` | instructor |
| `students` | package, tests, docs, **stub** notebooks; own history, no solutions in it | students |

The course site is deployed from `master` but always serves the student
notebooks (the Pages workflow builds them from these sources).

## Local files and git

* `scripts/check_all.sh` runs everything into `_check/` (ignored) and turns
  on the notebook filter below. `--site` also builds the course site into
  `_check/site`, only to prove it builds; the real site is built by CI.
  To preview it locally: `mkdocs serve`, then open http://127.0.0.1:8000.
* Notebooks go through a git clean filter (`.gitattributes`, `scripts/nbclean.py`)
  that drops outputs and execution counts, so running them does not change
  what git stores. `check_all.sh` enables it; by hand:
  `git config filter.nbclean.clean "python3 scripts/nbclean.py"`. If
  `git status` still lists a notebook you only ran, `git add labs` refreshes it.
* Team submissions go in `submissions/` (tracked, master only).
  `python scripts/collect_pareto.py submissions/ --show` draws the class plot
  into `submissions/class_pareto.png` (ignored). Lab 4 itself writes
  `labs/submission.json`, which is ignored.

## Changing a lab

Each `labN_*.txt` here is one notebook, with the reference solution inside
`### BEGIN SOLUTION` / `### END SOLUTION` markers (format described in
`scripts/build_notebooks.py`).

1. Edit the source, then `python scripts/build_notebooks.py --solutions`.
2. If a task or its inputs changed: `python scripts/make_expected.py`.
3. `scripts/check_all.sh` must end with ALL GOOD. Commit on `master`.
4. `scripts/sync_students.sh "Short message"` updates the `students` branch.
5. `git checkout solutions && git merge --ff-only master && git checkout master`.
6. `git push origin master solutions students`.

To start the separate student repository, push only that branch:
`git push <student-repo-url> students:main`. Then update the Colab and site
links in `docs/` and in `scripts/build_notebooks.py` to the new repository.

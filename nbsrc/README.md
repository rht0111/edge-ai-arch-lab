# Instructor notes (master and solutions only)

## Branches

| Branch | Contents | Who sees it |
|---|---|---|
| `master` | everything: package, solved notebooks, notebook sources, scripts | instructor |
| `solutions` | same as `master` | instructor |
| `students` | package, tests, docs, **stub** notebooks; own history, no solutions in it | students |

The course site is deployed from `master` but always serves the student
notebooks (the Pages workflow builds them from these sources).

## Changing a lab

Each `labN_*.txt` here is one notebook, with the reference solution inside
`### BEGIN SOLUTION` / `### END SOLUTION` markers (format described in
`scripts/build_notebooks.py`).

1. Edit the source, then `python scripts/build_notebooks.py --solutions`.
2. If a task or its inputs changed: `python scripts/make_expected.py`.
3. `pytest tests` must pass. Commit on `master`.
4. `scripts/sync_students.sh "Short message"` updates the `students` branch.
5. `git checkout solutions && git merge --ff-only master && git checkout master`.
6. `git push origin master solutions students`.

To start the separate student repository, push only that branch:
`git push <student-repo-url> students:main`. Then update the Colab and site
links in `docs/` and in `scripts/build_notebooks.py` to the new repository.

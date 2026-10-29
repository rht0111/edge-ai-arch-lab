# Instructor notes (master and solutions only)

## Branches

| Branch | Contents | Who sees it |
|---|---|---|
| `master` | everything, including the package, solved notebooks, notebook sources and scripts | instructor |
| `solutions` | same as `master` | instructor |
| `students` | package, tests, docs and **stub** notebooks, with its own history and no solutions in it | students |

The course site of this repository is deployed from `master` but always serves
the student notebooks, which the Pages workflow builds from these sources.

## Local files and git

* `scripts/check_all.sh` runs everything into `_check/` (ignored) and turns
  on the notebook filter below. With `--site` it also builds the course site
  into `_check/site`, only to prove that it builds. The real site is built by
  CI. To preview it locally, run `mkdocs serve` and open http://127.0.0.1:8000.
* Notebooks go through a git clean filter (`.gitattributes`,
  `scripts/nbclean.py`) that drops outputs and execution counts, so running
  them does not change what git stores. `check_all.sh` enables it, or by hand
  run `git config filter.nbclean.clean "python3 scripts/nbclean.py"`. If
  `git status` still lists a notebook you only ran, `git add labs` refreshes it.
* Team submissions go in `submissions/` (tracked, master only).
  `python scripts/collect_pareto.py submissions/ --show` draws the class plot
  into `submissions/class_pareto.png` (ignored). Lab 4 itself writes
  `labs/submission.json`, which is ignored.

## Changing a lab

Each `labN_*.txt` here is one notebook, with the reference solution between
`### BEGIN SOLUTION` and `### END SOLUTION` markers (the format is described
in `scripts/build_notebooks.py`).

1. Edit the source, then run `python scripts/build_notebooks.py --solutions`.
2. If a task or its inputs changed, run `python scripts/make_expected.py`.
3. `scripts/check_all.sh` must end with ALL GOOD. Commit on `master`.
4. `scripts/sync_students.sh "Short message"` updates the `students` branch.
5. `git checkout solutions && git merge --ff-only master && git checkout master`.
6. `git push origin master solutions students`.

## The separate student repository

The `students` branch is standalone. It has its own workflows (from
`students_overlay/`), installs `archsim` from its own repository, and links
only to its own repository and site. `sync_students.sh` rewrites every link
for the repository and branch you give it. For a new repository `OWNER/NAME`
whose default branch is `main`, the steps are these.

1. Create the empty repository `OWNER/NAME` on GitHub.
2. `scripts/sync_students.sh --repo OWNER/NAME --branch main "Point links at OWNER/NAME"`
3. `git push https://github.com/OWNER/NAME.git students:main`
4. In that repository, set Settings → Pages → Source to "GitHub Actions" and
   run the `pages` workflow once.

After step 2 the `students` branch here points at the new repository, so run
the same command again (with the same options) whenever you sync later. The
students repository then serves its own site at `https://OWNER.github.io/NAME/`.

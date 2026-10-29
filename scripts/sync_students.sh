#!/usr/bin/env bash
# Update the students branch from master. It gets the same package, tests and
# docs, stub notebooks and its own simple workflows (students_overlay/), and
# none of the instructor files. The branch keeps its own history and is never
# merged with master, so no solution ever appears in it. Every link and the
# Colab install command point at the repository given with --repo, so the
# branch works on its own once pushed there.
#
#   scripts/sync_students.sh "Commit message"
#   scripts/sync_students.sh --repo OWNER/NAME --branch main "Commit message"
#
# The defaults (this repository, branch students) keep the copy here usable.
set -euo pipefail

repo="rht0111/edge-ai-arch-lab"
branch="students"
while [ $# -gt 1 ]
do
    case "$1" in
        --repo) repo="$2"; shift 2 ;;
        --branch) branch="$2"; shift 2 ;;
        *) break ;;
    esac
done
message="${1:-Update from master}"

root=$(git rev-parse --show-toplevel)
cd "$root"
[ "$(git rev-parse --abbrev-ref HEAD)" = master ] || { echo "run this on master"; exit 1; }
git diff --quiet && git diff --cached --quiet || { echo "commit your changes first"; exit 1; }

INSTRUCTOR_ONLY='^(nbsrc/|students_overlay/|submissions/|labs/|scripts/(build_notebooks|make_expected|check_all|sync_students)\.|\.github/workflows/)'

tmp=$(mktemp -d)
trap 'git worktree remove --force "$tmp" 2>/dev/null || true; rm -rf "$tmp"' EXIT
git worktree add -q "$tmp" students

(cd "$tmp" && git ls-files -z | xargs -0 -r git rm -q)
git ls-files | grep -vE "$INSTRUCTOR_ONLY" | xargs -d '\n' cp --parents -t "$tmp"
(cd students_overlay && find . -type f | xargs -d '\n' cp --parents -t "$tmp")
python3 scripts/build_notebooks.py --stubs --out "$tmp/labs" > /dev/null
for nb in "$tmp"/labs/*.ipynb; do
    grep -q NotImplementedError "$nb" || { echo "$nb looks solved, aborting"; exit 1; }
done

python3 - "$tmp" "$repo" "$branch" <<'PY'
import sys
from pathlib import Path

tree, repo, branch = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
owner, name = repo.split("/")
here = "rht0111/edge-ai-arch-lab"
rules = [
    (f"github.com/{here}/blob/students/", f"github.com/{repo}/blob/{branch}/"),
    (f"archsim @ git+https://github.com/{here}", f"archsim @ git+https://github.com/{repo}@{branch}"),
    ("rht0111.github.io/edge-ai-arch-lab", f"{owner}.github.io/{name}"),
    (f"github.com/{here}", f"github.com/{repo}"),
    (f"repo_name: {here}", f"repo_name: {repo}"),
    ("cd edge-ai-arch-lab", f"cd {name}"),
    ("`edge-ai-arch-lab` folder", f"`{name}` folder"),
]
for f in tree.rglob("*"):
    if not f.is_file() or ".git" in f.parts or f.name.startswith("LICENSE") or f.suffix == ".png":
        continue
    text = f.read_text()
    new = text
    for old, rep in rules:
        new = new.replace(old, rep)
    if new != text:
        f.write_text(new)
PY

cd "$tmp"
git add -A
if git diff --cached --quiet; then
    echo "students is already up to date"
else
    git commit -qm "$message"
    git log --oneline -1
fi

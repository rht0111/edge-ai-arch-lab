#!/usr/bin/env bash
# Update the students branch from master: same package, tests and docs,
# stub notebooks, and none of the instructor files. The students branch keeps
# its own history (it is never merged with master), so no solution ever
# appears in it and it can be pushed as-is to a separate repository.
#
#   scripts/sync_students.sh "Message for the students commit"
set -euo pipefail

root=$(git rev-parse --show-toplevel)
cd "$root"
[ "$(git rev-parse --abbrev-ref HEAD)" = master ] || { echo "run this on master"; exit 1; }
git diff --quiet && git diff --cached --quiet || { echo "commit your changes first"; exit 1; }

INSTRUCTOR_ONLY='^(nbsrc/|scripts/build_notebooks\.py|scripts/make_expected\.py|scripts/sync_students\.sh|scripts/check_all\.sh|labs/)'

tmp=$(mktemp -d)
trap 'git worktree remove --force "$tmp" 2>/dev/null || true; rm -rf "$tmp"' EXIT
git worktree add -q "$tmp" students

(cd "$tmp" && git ls-files -z | xargs -0 -r git rm -q)
git ls-files | grep -vE "$INSTRUCTOR_ONLY" | xargs -d '\n' cp --parents -t "$tmp"
python scripts/build_notebooks.py --stubs --out "$tmp/labs" > /dev/null
for nb in "$tmp"/labs/*.ipynb; do
    grep -q NotImplementedError "$nb" || { echo "$nb looks solved, aborting"; exit 1; }
done

cd "$tmp"
git add -A
if git diff --cached --quiet; then
    echo "students is already up to date"
else
    git commit -qm "${1:-Update from master}"
    git log --oneline -1
fi

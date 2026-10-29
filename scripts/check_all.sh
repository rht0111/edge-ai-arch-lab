#!/usr/bin/env bash
# Run everything on master (or solutions) and report what passed.
#   scripts/check_all.sh            # tests, notebooks, class Pareto plot
#   scripts/check_all.sh --site     # also build the course site (needs .[docs])
# Executed notebooks and plots go to _check/ (ignored by git).
set -uo pipefail
cd "$(git rev-parse --show-toplevel)"
# store notebooks without outputs (see scripts/nbclean.py), harmless if already set
git config filter.nbclean.clean >/dev/null || git config filter.nbclean.clean "python3 scripts/nbclean.py"
out=_check
rm -rf "$out"; mkdir -p "$out/executed" "$out/submissions"
fail=0
step() { printf '\n== %s\n' "$1"; }
result() { if [ "$1" -eq 0 ]; then echo "   OK"; else echo "   FAILED"; fail=1; fi; }

step "archsim unit tests"
python -m pytest tests/unit -q; result $?

step "lab checks against the stored expected values"
python -m pytest tests -q --ignore=tests/unit; result $?

step "every notebook, top to bottom"
for nb in labs/*.ipynb; do
    start=$(date +%s)
    python -m jupyter nbconvert --to notebook --execute "$nb" --output-dir "$out/executed" \
        --ExecutePreprocessor.timeout=120 --log-level=ERROR
    rc=$?
    printf '   %-34s %3ss  %s\n' "$(basename "$nb")" "$(( $(date +%s) - start ))" \
        "$([ $rc -eq 0 ] && echo ok || echo FAILED)"
    [ $rc -eq 0 ] || fail=1
done

step "class Pareto plot from sample submissions"
python - "$out/submissions" <<'PY'
import sys
from archsim.design import Design, make_submission, save_submission
designs = {"baseline": Design(), "units-4": Design(softmax_lanes=4, gelu_lanes=4),
           "small-8x8": Design(8, 64, 8, 4, 4), "int4-32x32": Design(32, 64, 4, 4, 4),
           "big-buffer": Design(16, 256, 8, 8, 8)}
for team, d in designs.items():
    save_submission(make_submission(team, d), f"{sys.argv[1]}/{team}.json")
PY
cp labs/submission.json "$out/submissions/from-lab4.json" 2>/dev/null
python scripts/collect_pareto.py "$out/submissions" -o "$out/class_pareto.png"; result $?

if [ "${1:-}" = "--site" ]; then
    step "course site"
    python -m mkdocs build --strict -q -d "$out/site"; result $?
fi

printf '\n%s\n' "$([ $fail -eq 0 ] && echo 'ALL GOOD' || echo 'SOMETHING FAILED (see above)')"
echo "executed notebooks: $out/executed/   class plot: $out/class_pareto.png"
exit $fail

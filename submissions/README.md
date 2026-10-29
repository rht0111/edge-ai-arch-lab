# Team submissions

Put the `submission.json` file of each team here, renamed after the team
(for example `team-a.json`). These files are kept in git, the class plot is not.

```bash
python scripts/collect_pareto.py submissions/ --show   # also writes submissions/class_pareto.png
```

Every metric is recomputed from the design in each file, so a hand-edited
number has no effect.

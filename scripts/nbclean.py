"""Git clean filter for notebooks: drop outputs, execution counts and UI metadata.

Running a notebook rewrites it with outputs and execution counts. With this
filter, git compares and commits only what was written in the cells, so a
notebook that was merely run shows as unmodified. Enable it once per clone:

    git config filter.nbclean.clean "python3 scripts/nbclean.py"

(.gitattributes already routes *.ipynb through it.) Standard library only.
"""

import json
import sys

KEEP_NOTEBOOK_META = ("kernelspec", "language_info", "lab_policy")


def _lines(text):
    if isinstance(text, list):
        text = "".join(text)
    return text.splitlines(keepends=True)


def clean(nb: dict) -> dict:
    meta = nb.get("metadata", {})
    nb["metadata"] = {k: meta[k] for k in KEEP_NOTEBOOK_META if k in meta}
    if "language_info" in nb["metadata"]:
        nb["metadata"]["language_info"] = {"name": nb["metadata"]["language_info"].get("name", "python")}
    for cell in nb.get("cells", []):
        tags = cell.get("metadata", {}).get("tags")
        cell["metadata"] = {"tags": tags} if tags else {}
        cell["source"] = _lines(cell.get("source", ""))
        if cell.get("cell_type") == "code":
            cell["outputs"] = []
            cell["execution_count"] = None
        if not cell.get("attachments"):
            cell.pop("attachments", None)
    return nb


def main() -> None:
    raw = sys.stdin.read()
    try:
        nb = json.loads(raw)
    except ValueError:            # not a notebook we understand: pass it through untouched
        sys.stdout.write(raw)
        return
    sys.stdout.write(json.dumps(clean(nb), sort_keys=True, indent=1, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()

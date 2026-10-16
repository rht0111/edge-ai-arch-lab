# Setup

The labs need Python 3.10 or newer with `numpy`, `matplotlib` and
`ipywidgets`. No GPU, no deep learning framework, no Docker.

## A. In the browser (JupyterLite)

Open the [lab environment](https://rht0111.github.io/edge-ai-arch-lab/lite/lab/index.html?path=lab0_profile.ipynb).
The first visit downloads the Python runtime (about 30 MB), which can take a
minute on a busy network; later visits use the browser cache.

Run the first cell of each notebook: it installs `archsim` into the browser
session. Your edits are saved in the browser's local storage, per site and per
browser.

* To keep a notebook or `submission.json`, right-click it in the file browser
  and choose **Download**.
* Private or incognito windows forget everything when closed.
* If a notebook seems stuck, use *Kernel → Restart Kernel* and run the cells again.

## B. Google Colab

Click the *Open in Colab* badge at the top of a notebook. The first cell
installs `archsim` from GitHub. You need a Google account; save a copy to your
Drive to keep your work.

## C. Local install

```bash
git clone https://github.com/rht0111/edge-ai-arch-lab.git
cd edge-ai-arch-lab
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[lab]"          # archsim + JupyterLab
jupyter lab labs/
```

With [uv](https://docs.astral.sh/uv/): `uv sync --extra lab` then
`uv run jupyter lab labs/`.

To check your answers from a terminal:

```bash
pip install -e ".[dev]"
pytest tests/test_lab1.py       # one lab
pytest tests/unit               # the archsim library itself
```

## Troubleshooting on university PCs

**No admin rights.** You do not need them: use a virtual environment as above,
or `pip install --user -e ".[lab]"`. If `python` is not found, try `py`
(Windows) or `python3`.

**Proxy or blocked PyPI.** Set the proxy for pip, e.g.
`pip install --proxy http://proxy.example:3128 -e ".[lab]"`, or use the browser
path, which only needs access to this site and `cdn.jsdelivr.net`.

**JupyterLite stays on "Loading" or the kernel never starts.** Some network
filters block `cdn.jsdelivr.net`, from which the Python runtime is fetched.
Switch to Colab or a local install. Very old browsers are not supported; use
a recent Firefox, Chrome or Edge.

**The slider in Lab 2 does not move.** Widgets need `ipywidgets` 8 in the
same environment as JupyterLab. Locally, `pip install -U ipywidgets` and
restart JupyterLab. The rest of the lab works without the animation.

**`ModuleNotFoundError: archsim`.** The notebook kernel is not the
environment where you installed it. In JupyterLab pick the right kernel, or
run `%pip install -e ..` from a cell in `labs/`.

**Disk quota full on a network home directory.** Create the virtual
environment on a local disk (for example `/tmp` or `C:\Temp`), or use the
browser path.

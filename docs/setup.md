# Setup

There are three ways to do the labs. They give the same results, so pick one.

| | A. Browser (JupyterLite) | B. Google Colab | C. Your own computer |
|---|---|---|---|
| Install | nothing | nothing | Python + a few packages |
| Account | none | Google account | none |
| Where your work is saved | in this browser only | your Google Drive (if you save a copy) | files on your disk |
| Best for | the session itself | if A is blocked on your network | working offline, editing the code |

If you have never used a notebook, read [Notebooks in five minutes](#notebooks-in-five-minutes)
first. It takes five minutes and saves twenty.

## Notebooks in five minutes

A **notebook** (`.ipynb` file) is a page made of **cells**, one under the other.

* A **text cell** contains explanations, like this page.
* A **code cell** contains Python. It has a grey background and `[ ]` on its left.

To **run** a code cell, click inside it and press **Shift + Enter**. The
result (text, a table or a plot) appears just below it, and the cursor moves
to the next cell. While a cell runs, its label shows `[*]`. When it is done,
the label shows a number such as `[5]`, the order in which cells were run.

A few things to know follow.

* **Run cells from top to bottom.** A cell can use what earlier cells
  defined. If you get `NameError: name '...' is not defined`, an earlier cell
  has not been run, so run everything above it again.
* **Run all at once** with the menu *Run → Run All Cells* (JupyterLab) or
  *Runtime → Run all* (Colab).
* **Start again cleanly** with *Kernel → Restart Kernel and Run All Cells*
  (in Colab, *Runtime → Restart and run all*). The **kernel** is the Python
  process behind the notebook, and restarting it forgets every variable.
* **Edit a cell** by clicking in it and typing. Run it again (Shift + Enter)
  to see the effect.
* **Red text is an error message.** Read the last line first.

Here is what you will see in these labs.

* `# TODO` marks the code you write. Until you do, the function contains
  `raise NotImplementedError("TODO")`, so running it, or a later cell that
  uses it, shows a red `NotImplementedError: TODO`. That is expected and means
  "this is your task".
* After each task there is a `check(...)` cell. It prints `PASS (n cases)`,
  `not implemented yet`, or `FAIL on case ...` with the expected and the
  actual values.
* The first code cell of every notebook is a **setup cell**. Run it first,
  every time you open the notebook.

## A. In the browser (JupyterLite)

There is nothing to install. Python runs inside your browser tab. Use a
recent Firefox, Chrome or Edge, and not a private window, which forgets your work.

1. Open **[the lab environment](https://rht0111.github.io/edge-ai-arch-lab/lite/lab/index.html?path=lab0_profile.ipynb)**.
   JupyterLab appears, with a file list on the left (the five labs) and the
   open notebook on the right.
2. Wait until the circle at the top right of the notebook, next to
   *Python (Pyodide)*, is hollow (idle). The first visit downloads Python
   (about 30 MB), which can take a minute. Later visits are faster.
3. Click in the first code cell (the setup cell) and press **Shift + Enter**.
   It installs `archsim` inside the browser in 10 to 30 seconds and prints
   nothing when it succeeds.
4. Work down the notebook with Shift + Enter, reading as you go. Do the
   `# TODO` tasks and run the `check(...)` cell after each one.
5. To open another lab, double-click it in the file list on the left. If the
   list is hidden, click the folder icon in the far-left bar.

Saving and getting files out works as follows.

* Your edits are saved automatically **in this browser on this computer**
  (also with *File → Save*, or Ctrl + S). Another browser or computer will not see them.
* To keep a copy, right-click the notebook in the file list and choose **Download**.
  Lab 4 writes `submission.json` in the same list. Right-click it, choose
  **Download**, then hand it in as instructed.
* To get a fresh copy of a lab, right-click it, choose **Delete**, then reload the page.

If something goes wrong, check these first.

* **The kernel never becomes idle, or the page says "Loading" forever.** Your
  network probably blocks `cdn.jsdelivr.net`. Use Colab (B) or your own computer (C).
* **A cell runs forever or the page freezes.** Use *Kernel → Restart Kernel*,
  then run the setup cell again and the cells you need.
* **`ModuleNotFoundError: No module named 'archsim'`.** The setup cell was not
  run after the last restart. Run it.

## B. Google Colab

Colab runs the notebook on a Google server. You need a Google account.

1. Open the lab page on this site (for example [Lab 0](labs/lab0.md)) and
   click **Open in Colab**, or click the *Open in Colab* badge at the top of
   the notebook.
2. Sign in with your Google account if asked.
3. **Save your own copy first** with *File → Save a copy in Drive*. Colab
   opens the copy in a new tab, and that is the tab to work in. Otherwise your
   changes are lost when you close the page.
4. Run the setup cell (click it and press Shift + Enter, or click the round
   play button on its left). Colab shows *"Warning, this notebook was not
   authored by Google"*, so click **Run anyway**. The cell installs `archsim`
   from GitHub in about 30 seconds. If Colab then shows a **Restart session**
   button, click it and run the setup cell once more.
5. Work down the notebook with Shift + Enter, as in A.

To get files out (Lab 4), click the **folder icon** in the left bar, find
`submission.json` (click the refresh icon if it is not there), click the three
dots next to it and choose **Download**.

If something goes wrong, check these first.

* **The slider in Lab 2 does not appear.** Run the cell again. If it still
  does not appear, skip it, because the rest of the lab does not need it.
* **Runtime disconnected** (after a long pause). Use *Runtime → Run all*.
  Everything is recomputed in under a minute.

## C. On your own computer

You need Python 3.10 or newer and about 500 MB of disk space. The commands
below are typed in a **terminal**. On Ubuntu press Ctrl + Alt + T, on macOS
open the *Terminal* app, and on Windows open *Anaconda Prompt* or *PowerShell*.

### Step 1. Get the files

```bash
git clone https://github.com/rht0111/edge-ai-arch-lab.git
cd edge-ai-arch-lab
```

If you do not have git, click **Code → Download ZIP** on the GitHub page,
unzip it and `cd` into the folder.

### Step 2. Create a clean Python environment

An *environment* is a private copy of Python for this course, so that
nothing clashes with other software. Use **one** of the two options.

**Option 1, if you use Anaconda or Miniconda** (your prompt starts with `(base)`).

```bash
conda create -n edgeai python=3.12 -y
conda activate edgeai
```

Your prompt now starts with `(edgeai)`. Next time, only `conda activate edgeai` is needed.

**Option 2, with plain Python** (no conda).

```bash
python3 -m venv .venv
source .venv/bin/activate          # on Windows, .venv\Scripts\activate
```

Your prompt now starts with `(.venv)`. Next time, only the `source` line is
needed, from inside the `edge-ai-arch-lab` folder.

!!! warning "Do not mix the two"
    Never have `(base)` and `(.venv)` active at the same time, and never run
    `python3 -m venv .venv` on top of an existing `.venv`. Both produce a
    broken environment with errors such as `No module named 'math'` or
    `No module named '_posixsubprocess'`. The fix is in
    [Troubleshooting](#troubleshooting).

### Step 3. Install the course package and JupyterLab

```bash
pip install -e ".[lab,dev]"
```

This takes one or two minutes. Then check that it worked.

```bash
python -c "import archsim; print('archsim', archsim.__version__, 'is ready')"
pytest tests/unit -q
```

The first command prints `archsim 0.1.0 is ready`, and the second ends with `48 passed`.

### Step 4. Open the labs

```bash
jupyter lab labs/
```

Your browser opens JupyterLab (at `http://localhost:8888`). Double-click
`lab0_profile.ipynb` in the file list and work as described in
[Notebooks in five minutes](#notebooks-in-five-minutes). On your own computer
the setup cell does nothing, which is normal.

**Keep the terminal open while you work.** To stop JupyterLab, save your
notebooks, then press Ctrl + C twice in the terminal.

### Keeping your clone clean (if you use git)

Running a notebook saves its outputs into the `.ipynb` file. Tell git, once
per clone, to ignore outputs and keep only what you wrote in the cells.

```bash
git config filter.nbclean.clean "python3 scripts/nbclean.py"
```

After that, `git diff` shows only your real edits. `git status` may still
list a notebook you merely ran. `git add labs` refreshes it without staging
anything, and `git restore labs` throws away your outputs and edits.

### Step 5 (optional). Check your answers from the terminal

Open a second terminal, activate the environment again, and run the checks of one lab.

```bash
pytest tests/test_lab0.py
```

Each lab has its own file. A task reports `not implemented yet` and fails
until you complete it, and once all its tasks are done the file passes.

## Troubleshooting

**`No module named 'math'`, `No module named '_posixsubprocess'` or similar,
just after creating an environment.** The environment mixes two Pythons
(usually conda's and the system's). Delete it and start Step 2 again with
only one of them active.

```bash
deactivate 2>/dev/null
conda deactivate 2>/dev/null
rm -rf .venv
# then Step 2 (Option 1 or Option 2) and Step 3
```

**pip prints a long warning about "pip's dependency resolver", followed by
`torch ... requires ...`** (or another package you never asked for). This is a warning about software already on your computer,
not about the course, and the install has finished. It means the environment
can see packages installed elsewhere, usually with `pip install --user` into
your home folder. Make the course environment ignore them, then install again.

```bash
conda env config vars set PYTHONNOUSERSITE=1 -n edgeai   # conda (Option 1)
conda deactivate && conda activate edgeai
pip install -e ".[lab,dev]"
```

With a venv (Option 2), recreate it with `python3 -m venv --clear .venv` and
run `export PYTHONNOUSERSITE=1` before activating it. Either way, if
`pytest tests/unit -q` ends with `48 passed`, everything the course needs works.

**`git pull` stops with "Your local changes to the following files would be
overwritten by merge" and lists notebooks.** The notebooks only contain the
outputs of your runs. Keep a copy of any notebook you edited and want to
keep, then discard the local changes and pull again.

```bash
git restore labs/
git pull
```

**`jupyter: command not found` or `Command 'jupiter' not found`.** The command
is `jupyter` (with a y), and it exists only while the environment is active.
Check that your prompt starts with `(edgeai)` or `(.venv)`.

**`ModuleNotFoundError: No module named 'archsim'` in a notebook.** JupyterLab
was started from another environment. Stop it (Ctrl + C twice), activate the
course environment, and run `jupyter lab labs/` again.

**`error: externally-managed-environment` from pip.** You are installing
outside an environment. Do Step 2 first.

**No admin rights on a university PC.** You do not need them, because both
options of Step 2 work without. If `python3` is not found, try `python` (or
`py` on Windows).

**Proxy or blocked PyPI.** Run `pip install --proxy http://proxy.example:3128 -e ".[lab,dev]"`
with your proxy's address, or use the browser (A).

**The folder is on a USB disk or network share and creating the
environment fails.** Use conda (Option 1), which stores the environment in
your home folder, or create the venv there with
`python3 -m venv ~/venvs/edgeai && source ~/venvs/edgeai/bin/activate`.

**Disk quota full on a network home directory.** Create the environment on a
local disk (for example `/tmp` or `C:\Temp`), or use the browser (A).

**The slider in Lab 2 does not move (local install).** Run `pip install -U ipywidgets`
in the active environment, then restart JupyterLab. The rest of the lab works
without the animation.

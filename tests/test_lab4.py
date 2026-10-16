"""Checks for Lab 4. Run with: pytest tests/test_lab4.py"""

import pytest

from archsim.checks import check
from nbtasks import TASKS, load, tasks_of


@pytest.mark.parametrize("task", tasks_of("lab4"))
def test_task(task):
    notebook, name = TASKS[task]
    assert check(task, load(notebook)[name])


def test_design_within_budget():
    from archsim.design import evaluate
    d = load("lab4_design_challenge")["my_design"]
    assert evaluate(d)["within_budget"]

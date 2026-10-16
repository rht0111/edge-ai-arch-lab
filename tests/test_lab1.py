"""Checks for Lab 1. Run with: pytest tests/test_lab1.py"""

import pytest

from archsim.checks import check
from nbtasks import TASKS, load, tasks_of


@pytest.mark.parametrize("task", tasks_of("lab1"))
def test_task(task):
    notebook, name = TASKS[task]
    assert check(task, load(notebook)[name])

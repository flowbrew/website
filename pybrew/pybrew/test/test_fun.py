import pytest
import tempfile
import os
import glob
from path import Path
from pybrew import my_fun, notification, run, pipe, map, comp, force


def test_my_fun():
    assert my_fun(4) == 5

import pytest
import tempfile
import os
from path import Path
from pybrew import my_fun, notification, run_io, pipe, map, comp, force, try_n_times_decorator


def test_my_fun():
    assert my_fun(4) == 5


def test_try_n_times_decorator():
    global n
    n = 5

    @try_n_times_decorator(5, 0)
    def unreliable_io():
        global n
        n = n - 1
        if n > 0:
            raise Exception('Fail!')
        return 'OK'

    @try_n_times_decorator(5, 0)
    def broken_io():
        raise Exception('Fail!')

    assert unreliable_io() == 'OK'

    with pytest.raises(Exception) as e:
        broken_io()
    assert 'Fail!' in str(e.value)

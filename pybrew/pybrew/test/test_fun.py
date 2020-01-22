import pytest
import tempfile
import os
from path import Path
from pybrew import my_fun, notification_io, run_io, pipe, map, comp, force, try_n_times_decorator, tmp


def test_my_fun():
    assert my_fun(4) == 5


def test_working_directory_context_manager():
    with tmp() as a, tmp() as b:
        with Path(a):
            run_io('echo aaa > a.txt')
        with Path(b):
            run_io('echo bbb > b.txt')

        with Path(a):
            assert open('a.txt', 'r').read() == 'aaa\n'
        with Path(b):
            assert open('b.txt', 'r').read() == 'bbb\n'


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

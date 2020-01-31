import pytest
import tempfile
import os
from path import Path
from pybrew import my_fun, notification_io, run_io, pipe, map, comp, force, try_n_times_decorator, tmp, extract_repo_name_from_origin, dict_to_filesystem_io, filesystem_to_dict_io, copy_dir_io, wait_until_html_deployed_io


@pytest.mark.pybrew
def test_my_fun():
    assert my_fun(4) == 5


@pytest.mark.slow
@pytest.mark.pybrew
def test_wait_until_html_deployed_io():
    wait_until_html_deployed_io(
        'https://example.com',
        lambda soup:
            'Example Domain' in soup.find('h1').text
    )


@pytest.mark.pybrew
def test_extract_repo_name_from_origin():
    for origin in [
        'git@github.com:flowbrew/website.git',
        'https://github.com/flowbrew/website'
    ]:
        org, name = extract_repo_name_from_origin(origin)
        assert org == 'flowbrew'
        assert name == 'website'


@pytest.mark.pybrew
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


@pytest.mark.pybrew
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


@pytest.mark.pybrew
def test_copy_dir_io():
    filesystem = {
        'lol': b'internet',
        'lol2/lol': b'some internet'
    }

    with tmp() as td1, tmp() as td2:
        dict_to_filesystem_io(td1, filesystem)

        dst = os.path.join(td2, '/results')
        copy_dir_io(td1, dst)
        assert filesystem_to_dict_io(dst) == filesystem

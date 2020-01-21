import pytest
import tempfile
import os
from path import Path
from pybrew import build_jekyll_io, dict_to_filesystem_io, run
from bs4 import BeautifulSoup


def test_build_jekyll_io():
    return 
    filesystem = {
        '.git/empty/dir': None,
        'hello/world/file1': '123123',
        'hello/world/file2': b'\x1231231232',
        'something': '16',
    }

    with tempfile.TemporaryDirectory() as td:
        dict_to_filesystem_io(td, filesystem)

        with Path(td):

            run('jekyll new .')
            run('ls -a')

            assert False

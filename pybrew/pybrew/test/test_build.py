import pytest
import tempfile
import os
import yaml
from path import Path
from pybrew import build_jekyll_io, dict_to_filesystem_io, run, tmp
from bs4 import BeautifulSoup


def test_build_jekyll_io(BRANCH, SHA):
    return
    with tmp() as source, tmp() as dest:
        run(f'jekyll new --force {source}')

        build_jekyll_io(source, dest, SHA, BRANCH)

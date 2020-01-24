import os
import pytest
import re
from pybrew import files_io, pipe, chain_, flatten, force, map, filterempty, filter
from bs4 import BeautifulSoup
from path import Path


@pytest.mark.build
def test_baked_images(WEBSITE_BUILD_PATH):
    def _validate_path(path):
        with Path(os.path.join(WEBSITE_BUILD_PATH, 'assets')):
            assert os.stat('.' + path).st_size > 0

    def __validate(soup):
        srcset = re.compile(r'.+')
        extract_path = re.compile(r'assets(/\S+)')
        pipe(
            soup.find_all('img', {'srcset': srcset}),
            map(lambda x: x.get('srcset').split(',') + [x.get('img')]),
            flatten,
            filterempty,
            filter(lambda x: not x.startswith('http')),
            map(lambda x: extract_path.search(x)),
            filterempty,
            map(lambda x: x.group(1)),
            map(_validate_path),
            force
        )

    def _validate(path):
        with open(path, 'rb') as f:
            html = f.read().decode('utf-8')
            soup = BeautifulSoup(html, features="html.parser")
            __validate(soup)

    [_validate(x) for x in files_io(WEBSITE_BUILD_PATH)
        if x.endswith('.html')]

import os
import pytest
import re
from pybrew import files_io, pipe, chain_, flatten, force, map, filterempty, filter, glvrd_proofread_io_cached
from bs4 import BeautifulSoup
from bs4.element import Comment
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


def extract_all_texts(html):
    soup = BeautifulSoup(html, features="html.parser")

    tags = soup.find_all(re.compile(r'^(p|h1|h2|h3|h4|li|figcaption)$'))
    texts = (
        x.get_text().strip('\n').strip().replace('\xa0', ' ') for x in tags
        if not isinstance(x, Comment)
    )

    return (x.replace('( )', '') for x in texts if x)


@pytest.mark.build
def test_texts_with_glvrd(WEBSITE_BUILD_PATH):
    def __validate(path, text):
        r = glvrd_proofread_io_cached(text)
        assert r['red'] >= 7.9
        assert r['blue'] >= 7.9

    def _validate(path):
        if any(x in path for x in [
            'политика+конфиденциальности',
        ]):
            return

        with open(path, 'rb') as f:
            html = f.read().decode('utf-8')
            [__validate(path, x) for x in extract_all_texts(html)]

    [_validate(x) for x in files_io(WEBSITE_BUILD_PATH)
        if x.endswith('.html')]


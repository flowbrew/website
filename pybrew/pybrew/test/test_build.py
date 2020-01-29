import os
import pytest
import re

from pybrew import files_io, pipe, chain_, flatten, force, map, filterempty, filter, glvrd_proofread_io, branch_to_prefix, master_branch, yandex_speller_io

from bs4 import BeautifulSoup
from bs4.element import Comment
from path import Path


def extract_all_htmls_io(path):
    def _make_soup_io(path):
        with open(path, 'rb') as f:
            html = f.read().decode('utf-8')
            soup = BeautifulSoup(html, features="html.parser")
            return (path, soup)

    return filterempty(
        _make_soup_io(x) for x in files_io(path) if x.endswith('.html')
    )


@pytest.mark.build
def test_baked_images_io(WEBSITE_BUILD_PATH):
    def _validate_path(path):
        with Path(os.path.join(WEBSITE_BUILD_PATH, 'assets')):
            assert os.stat('.' + path).st_size > 0

    def __validate(path, soup):
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

    [__validate(p, s) for p, s in extract_all_htmls_io(WEBSITE_BUILD_PATH)]


@pytest.mark.skip_in_local
@pytest.mark.build
def test_beseurl_on_branch_build_io(BRANCH, WEBSITE_BUILD_PATH):
    def _validate_href(path, href):
        if href.startswith('/') and BRANCH != master_branch():
            assert href.startswith('/' + branch_to_prefix(BRANCH))

    def __validate(path, soup):
        [
            _validate_href(path, x.get('href').strip())
            for x in soup.find_all('a')
        ]

    [__validate(p, s) for p, s in extract_all_htmls_io(WEBSITE_BUILD_PATH)]


def extract_all_texts(html):
    soup = BeautifulSoup(html, features="html.parser")

    tags = soup.find_all(re.compile(r'^(p|h1|h2|h3|h4|li|figcaption)$'))
    texts = (
        x.get_text().strip('\n').strip().replace('\xa0', ' ') for x in tags
        if not isinstance(x, Comment)
    )

    return (x.replace('( )', '') for x in texts if x)


def all_texts_io(path):
    def _get_text_io(path):
        if any(x in path for x in [
            'политика+конфиденциальности',
        ]):
            return

        with open(path, 'rb') as f:
            html = f.read().decode('utf-8')
            return (path, extract_all_texts(html))

    return filterempty(
        _get_text_io(x) for x in files_io(path) if x.endswith('.html')
    )


@pytest.mark.build
def test_texts_with_glvrd_io(WEBSITE_BUILD_PATH):
    def __validate_io(path, text):
        r = glvrd_proofread_io(text)
        assert r['red'] >= 7.9
        assert r['blue'] >= 7.9

    [
        [__validate_io(path, text) for text in texts]
        for path, texts in all_texts_io(WEBSITE_BUILD_PATH)
    ]


@pytest.mark.build
def test_texts_with_yandex_speller_io(WEBSITE_BUILD_PATH):
    def __validate_io(path, text):
        r = yandex_speller_io(text)
        assert len(r) == 0

    [
        [__validate_io(path, text) for text in texts]
        for path, texts in all_texts_io(WEBSITE_BUILD_PATH)
    ]

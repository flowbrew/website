import os
import pytest
import re

from pybrew import files_io, pipe, chain_, flatten, force, map, filterempty, filter, glvrd_proofread_io, branch_to_prefix, master_branch, yandex_speller_io, try_n_times_decorator, chain

from functools import lru_cache

from bs4 import BeautifulSoup
from bs4.element import Comment
from path import Path

import requests
from urllib.parse import unquote


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


@pytest.mark.build
@pytest.mark.skip_in_local
@pytest.mark.slow
def test_validate_website_links(WEBSITE_BUILD_PATH, BRANCH):
    def _extract_all_links(html):
        soup = BeautifulSoup(html, features="html.parser")
        img_links = chain(*[
            [
                y.split(' ')[0] for y in x.get('srcset', '').split(',')
            ] + [x.get('src')]
            for x in soup.find_all('img')
        ])
        hrefs = [x.get('href') for x in soup.find_all('a')]
        return pipe(
            chain(img_links, hrefs),
            map(lambda x: x.strip()),
            filterempty,
            list,
        )

    def _get_links_io(path):
        with open(path, 'rb') as f:
            html = f.read().decode('utf-8')
            return (path, _extract_all_links(html))

    links = filterempty(
        _get_links_io(x) for x
        in files_io(WEBSITE_BUILD_PATH)
        if x.endswith('.html')
    )

    @lru_cache
    def __validate_link_io(path, link_):
        link = unquote(link_)

        if link.startswith('mailto:') or link.startswith('#'):
            return

        def __unlink(l):
            _, ext = os.path.splitext(l)
            if not ext:
                if l.endswith('/'):
                    return l + 'index.html'
                else:
                    return l + '.html'
            else:
                return l

        if link.startswith('/'):
            if BRANCH != master_branch():
                assert link.startswith('/' + branch_to_prefix(BRANCH))
            with Path(WEBSITE_BUILD_PATH):
                link2 = __unlink(link)
                link3 = re.sub(rf'^/({branch_to_prefix(BRANCH)})', '', link2)
                assert os.stat('.' + link3).st_size > 0

        elif link.startswith('./'):
            with Path(os.path.split(path)[0]):
                link2 = __unlink(link)
                assert os.stat(link2).st_size > 0

        else:
            if 'www.jstage.jst.go.jp' in link:
                # dh key too small, unsecure connection, can't validate
                return

            @try_n_times_decorator(n=5, timeout=5)
            def _check_code_io():
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Mobile Safari/537.36',
                    'Cache-Control': 'no-cache, no-store, must-revalidate',
                    'Pragma': 'no-cache',
                    'Expires': '0',
                    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                    'accept-encoding': 'gzip, deflate, br',
                    'accept-language': 'en-GB,en;q=0.9,en-US;q=0.8,ru;q=0.7,it;q=0.6',
                    'sec-fetch-mode': 'navigate',
                    'sec-fetch-site': 'none',
                }
                assert requests.get(link, headers=headers).status_code == 200

            _check_code_io()

    [
        [__validate_link_io(path, link) for link in ls]
        for path, ls in links
    ]

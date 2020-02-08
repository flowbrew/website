import pytest
import tempfile
import os

import imaplib
import email
from email import policy
import time
from urllib.parse import unquote, urlparse
from statistics import stdev

from path import Path
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from pybrew import my_fun, notification_io, run_io, pipe, map, comp, force, b2p, tmp, applyw, inject_branch_to_deployment, dict_to_filesystem_io, filesystem_to_dict_io, random_str, deploy_to_github_io, http_get_io, delete_github_repo_io, branch_to_prefix, try_n_times_decorator, remove_branch_from_deployment, wait_until_deployed_by_sha_io, secret_io, google_test_page_speed_io, partial, google_test_page_seo_io, curry, product, master_branch, chrome_io, frequency, branch_prefix, url_join


def validate_logs_io(driver):
    for entry in driver.get_log('browser'):
        assert entry.get('level', '').lower() not in ['severe']


def get_url(driver, *args):
    return driver.get(url_join(*args))


def disable_google_analytics(driver, base):
    get_url(driver, base, 'disable_google_analytics')


def emails_io(addr, port, login, password):
    m = imaplib.IMAP4_SSL(addr, port)
    m.login(login, password)
    m.select()
    _, message_numbers = m.search(None, 'ALL')

    for num in message_numbers[0].split():
        _, data = m.fetch(num, '(RFC822)')

        msg = email.message_from_string(
            data[0][1].decode('utf-8'),
            policy=policy.default
        )

        yield {
            'from': msg['From'],
            'subject': msg['Subject'],
            'body': msg.get_payload(decode=True).decode(
                msg.get_content_charset()
            )
        }

    m.close()
    m.logout()


def url_path(driver):
    return urlparse(driver.current_url).path.strip()


def url(x):
    return unquote(x.current_url)


def i_want_to_test_split_test(TRAFFIC_ALLOCATION):
    if TRAFFIC_ALLOCATION:
        entry_point = '/?val=2'
        traffic_allocation = TRAFFIC_ALLOCATION
    else:
        entry_point = '/test_split_testing?val=2'
        traffic_allocation = {
            '': 0.2,
            'debug_split_test/a': 0.35,
            'debug_split_test/b': 0.45,
        }
    return entry_point, traffic_allocation

@pytest.mark.slow
@pytest.mark.deployment
def test_e2e_split_testing_traffic_allocation_io(URL, TRAFFIC_ALLOCATION):
    entry_point, traffic_allocation = i_want_to_test_split_test(
        TRAFFIC_ALLOCATION
    )

    url_allocation = {
        url_join(URL, k, entry_point): v
        for k, v in traffic_allocation.items()
    }

    def run_test():
        with chrome_io() as chrome:
            disable_google_analytics(chrome, URL)
            get_url(chrome, URL, entry_point)
            assert '404' not in chrome.title, "Page not found"
            validate_logs_io(chrome)
            return url(chrome)

    n = 15
    results_ = frequency(run_test() for _ in range(0, n))
    results = {k: v / n for k, v in results_.items()}

    assert set(results.keys()) == set(url_allocation.keys()), \
        "Didn't redirect on right pages or missing url params"

    # assert all(
    #     abs(results[k] - url_allocation[k]) < 0.15 for k in results.keys()
    # ), "Traffic distribution doesn't seem right"


@pytest.mark.slow
@pytest.mark.deployment
def test_e2e_split_testing_allocation_consistency_io(URL, TRAFFIC_ALLOCATION):
    entry_point, _ = i_want_to_test_split_test(
        TRAFFIC_ALLOCATION
    )

    def run_test():
        with chrome_io() as chrome:
            disable_google_analytics(chrome, URL)

            get_url(chrome, URL, entry_point)
            assert '404' not in chrome.title, "Page not found"
            first_url = url(chrome)

            def sub_test(chrome, first_url):
                get_url(chrome, URL, entry_point)
                assert first_url == url(chrome), \
                    "Split test traffic allocation is not consistent"

            [sub_test(chrome, first_url) for _ in range(0, 5)]
            validate_logs_io(chrome)

    [run_test() for _ in range(0, 10)]


@pytest.mark.deployment
@pytest.mark.not_in_branch
def test_e2e_404_redirect_io(URL):
    with chrome_io() as chrome:
        disable_google_analytics(chrome, URL)

        def assert_is_blog():
            assert url(chrome) in [
                url_join(URL, 'blog'),
                url_join(URL, 'blog') + '/'
            ]
            assert 'блог' in chrome.title.lower()

        get_url(chrome, URL, '/blog/nonexistent_article')
        assert_is_blog()

        branch = branch_prefix() + random_str()

        get_url(chrome, URL, branch, 'blog')
        assert_is_blog()

        get_url(chrome, URL, branch, 'blog', 'nonexistent_article')
        assert_is_blog()

        get_url(chrome, URL, branch, 'debug_split_test/a/test_split_testing')
        assert url(chrome) == url_join(
            URL, 'debug_split_test/a/test_split_testing'
        )
        assert 'Test split testing A' in chrome.title


@pytest.mark.slow
@pytest.mark.deployment
def test_e2e_checkout_io(URL):
    with chrome_io() as chrome:
        disable_google_analytics(chrome, base=URL)
        get_url(chrome, URL)
        chrome.find_element_by_id('buy-button-1').click()
        assert 'checkout' in url_path(chrome)

        token = random_str()

        WebDriverWait(chrome, 10).until(
            EC.presence_of_element_located((By.ID, 'name'))
        )

        chrome.find_element_by_id("name").send_keys(token)
        chrome.find_element_by_id("email").send_keys("bot@flowbrew.ru")
        chrome.find_element_by_id("phone").send_keys("9999999")
        chrome.find_element_by_xpath(
            "//*[@id='checkout_form']/div[2]/div[3]/div/input"
        ).click()
        chrome.find_element_by_id("address").send_keys("Улица 2 д2")
        chrome.find_element_by_id("coupon").send_keys("FLB10")
        chrome.find_element_by_id("comment").send_keys("Ignore, E2E test")
        chrome.find_element_by_id('buy').click()

        @try_n_times_decorator(n=5, timeout=15)
        def __check_email():
            emails = emails_io(
                'imap.yandex.ru', 993,
                secret_io('YANDEX_BOT_EMAIL'),
                secret_io('YANDEX_BOT_TOKEN')
            )
            assert any(
                token in x['body'] for x in emails
            ), 'Order wasnt received via '

        __check_email()

        assert 'спасибо' in url(chrome)
        validate_logs_io(chrome)


@pytest.mark.slow
@pytest.mark.pybrew
def test_selenium_io():
    with chrome_io() as chrome:
        chrome.get("http://www.python.org")
        assert 'Python'in chrome.title


@pytest.mark.pybrew
def test_remove_branch_from_deployment__remove_regular():
    branch_name = 'test'

    deployment_state = {
        b2p("master") + b2p("test") + 'index.html': 'overwritten index',
        b2p("master") + 'index.html': 'master index',
        b2p("test") + 'index.html': 'overwritten index',
        b2p("test") + 'delete.html': '2 delete',
        'index.html': 'master index',
    }

    result_state = {
        b2p("master") + b2p("test") + 'index.html': 'overwritten index',
        b2p("master") + 'index.html': 'master index',
        b2p("test") + 'index.html': 'overwritten index',
        'index.html': 'master index',
    }

    assert remove_branch_from_deployment(
        branch_name, deployment_state
    ) == result_state


@pytest.mark.pybrew
def test_remove_branch_from_deployment__remove_master():
    branch_name = 'master'

    deployment_state = {
        b2p("master") + b2p("test") + 'index.html': 'overwritten index',
        b2p("master") + 'index.html': 'master index',
        b2p("test") + 'index.html': 'overwritten index',
        b2p("test") + 'delete.html': '2 delete',
        'index.html': 'master index',
    }

    result_state = {
        b2p("test") + 'index.html': 'overwritten index',
        b2p("test") + 'delete.html': '2 delete',
    }

    assert remove_branch_from_deployment(
        branch_name, deployment_state
    ) == result_state


@pytest.mark.pybrew
def test_inject_branch_to_deployment__injecting_regular():
    branch_name = 'test'

    branch_state = {
        b2p("master") + 'index.html': 'test test',
        'index.html': 'test index new',
        'some/data': 'data new',
    }

    deployment_state = {
        b2p("master") + b2p("test") + 'index.html': 'overwritten index',
        b2p("master") + 'index.html': 'master index',
        b2p("test") + 'index.html': 'overwritten index',
        b2p("test") + 'delete.html': '2 delete',
        'index.html': 'master index',
    }

    result_state = {
        b2p("master") + b2p("test") + 'index.html': 'overwritten index',
        b2p("master") + 'index.html': 'master index',
        b2p("test") + b2p("master") + 'index.html': 'test test',
        b2p("test") + 'index.html': 'overwritten index',
        b2p("test") + 'some/data': 'data new',
        'index.html': 'master index',
    }

    assert inject_branch_to_deployment(
        branch_name, branch_state, deployment_state
    ) == result_state


@pytest.mark.pybrew
def test_inject_branch_to_deployment__injecting_master():
    branch_name = 'master'

    branch_state = {
        b2p("test") + 'index.html': 'overwritten index',
        'index.html': 'master index new',
        'some/data': 'some new master data',
    }

    deployment_state = {
        '.git/something': 'do not delete',
        '.git/empty/dir': None,
        b2p("master") + 'index.html': 'master index',
        b2p("master") + 'some/old/data': 'old data',
        b2p("master") + 'something': '123',
        b2p("test") + 'index.html': 'test index old',
        b2p("test") + 'some/data': 'data old',
        'index.html': 'master index',
        'some/old/data': 'old data',
        'something': '123',
    }

    result_state = {
        '.git/something': 'do not delete',
        '.git/empty/dir': None,
        b2p("master") + b2p("test") + 'index.html': 'overwritten index',
        b2p("master") + 'index.html': 'master index new',
        b2p("master") + 'some/data': 'some new master data',
        b2p("test") + 'index.html': 'overwritten index',
        b2p("test") + 'some/data': 'data old',
        'index.html': 'master index new',
        'some/data': 'some new master data',
    }

    assert inject_branch_to_deployment(
        branch_name, branch_state, deployment_state
    ) == result_state


@pytest.mark.pybrew
def test_dict_to_filesystem_io():
    filesystem = {
        '.git/empty/dir': None,
        'hello/world/file1': '123123',
        'hello/world/file2': b'\x1231231232',
        'something': '16',
    }

    def validate_file_io(path, content):
        if content is None:
            return os.path.isdir(path)
        with open(path, 'rb') as f:
            t = type(content)
            if t == str:
                return f.read().decode('utf-8') == content
            elif t == bytes:
                return f.read() == content
            else:
                return False

    def validate_filesystem_io(root, fs):
        return pipe(
            fs.items(),
            map(lambda x: (
                os.path.join(root, x[0]), x[1]
            )),
            map(applyw(validate_file_io)),
            all,
        )

    with tempfile.TemporaryDirectory() as td:
        dict_to_filesystem_io(td, filesystem)
        assert validate_filesystem_io(td, filesystem)


@pytest.mark.pybrew
def test_filesystem_to_dict_io():
    filesystem = {
        '.git/empty/dir': None,
        'hello/world/file1': b'123123',
        'hello/world/file2': b'\x1231231232',
        'something': b'16',
    }

    with tempfile.TemporaryDirectory() as td:
        dict_to_filesystem_io(td, filesystem)
        assert filesystem_to_dict_io(td) == filesystem


@pytest.mark.skip(reason="as slow as 300 s, doesn't worth it")
@pytest.mark.slow
@pytest.mark.pybrew
def test_deploy_to_github_io(
    ORGANIZATION,
    TEST_REPOSITORY,
    BRANCH,
    SHA
):
    data = f'''<!DOCTYPE html>
        <html>
        <head>
        <meta name="github-commit-sha" content="{SHA}" />
        </head>
        <body>
        {SHA}
        </body>
        </html>'''

    p1 = f'hello/{random_str()}.html'
    p1_ = branch_to_prefix('test') + p1

    deployment = [
        (
            'test',
            {
                p1: 'wrong data',
                'hello/world/file2': 'lol, internet',
                'something': '16',
                'index.html': SHA + ' is working',
                '404.html': 'page not found!',
            }
        ),
        (
            'master',
            {
                p1_: data,
                'freshly/created': data,
                'delete/test': 'file123',
                '404.html': 'master: page not found!',
            }
        ),
    ]

    for br, fs in deployment:
        with tmp() as td:
            dict_to_filesystem_io(td, fs)
            deploy_to_github_io(
                github_username=secret_io('GITHUB_WEBSITE_USERNAME'),
                github_token=secret_io('GITHUB_WEBSITE_TOKEN'),
                organization=ORGANIZATION,
                target_repo_name=TEST_REPOSITORY,
                branch=br,
                path=td
            )

    wait_until_deployed_by_sha_io(
        'https://' + ORGANIZATION + '.github.io/' +
        TEST_REPOSITORY + '/' + p1_.replace('.html', ''),
        SHA
    )


@pytest.mark.slow
@pytest.mark.skip_in_local
@pytest.mark.deployment
def test_website_performance_io(URL, BRANCH, SHA):
    def ___test_io(f, url, is_mobile):
        _f = comp(
            partial(sorted, key=lambda x: x[1]['score']),
            lambda x: x.items(),
            f
        )
        for name, audit in _f(
            google_pagespeed_key=secret_io('GOOGLE_PAGESPEED_KEY'),
            url=url,
            is_mobile=is_mobile,
            cookies={'split_test_master_sha': SHA}
        ):
            if name == 'uses-long-cache-ttl':
                assert audit['score'] >= 0.3

            elif name == 'is-crawlable':
                if BRANCH == master_branch():
                    assert audit['score'] >= 0.75

            elif is_mobile and name == 'first-contentful-paint-3g':
                assert audit['score'] >= 0.3

            elif is_mobile and name == 'first-cpu-idle':
                assert audit['score'] >= 0.4

            elif is_mobile and name == 'interactive':
                assert audit['score'] >= 0.4

            elif is_mobile and name == 'mainthread-work-breakdown':
                assert audit['score'] >= 0.6

            elif is_mobile and name == 'max-potential-fid':
                if url.endswith('checkout.html'):
                    assert audit['score'] >= 0.3
                else:
                    assert audit['score'] >= 0.4

            elif is_mobile and name == 'first-meaningful-paint':
                assert audit['score'] >= 0.7

            elif is_mobile and name == 'third-party-summary':
                assert audit['details']['summary']['wastedMs'] < 650

            elif is_mobile and name == 'total-blocking-time':
                assert audit['score'] >= 0.6

            else:
                assert audit['score'] >= 0.75

    tests = product(
        [google_test_page_speed_io, google_test_page_seo_io],
        [
            url_join(URL, '')
        ],
        [False, True],
    )

    [___test_io(*x) for x in tests]

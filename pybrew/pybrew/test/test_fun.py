import pytest
import tempfile
import os
from path import Path
from pybrew import my_fun, notification_io, run_io, pipe, map, comp, force, try_n_times_decorator, tmp, extract_repo_name_from_origin, dict_to_filesystem_io, filesystem_to_dict_io, copy_dir_io, wait_until_html_deployed_io, allocate_traffic, extract_key, pull_requests_io, secret_io, is_green_pull_request, is_stale_pull_request, split_test_label, s2t, tdlt, t2s, split_test_stale, deep_get, deep_set, deep_transform, labels_io


@pytest.mark.pybrew
def test_my_fun():
    assert my_fun(4) == 5


@pytest.mark.pybrew
def test_deep_get():
    dictionary = {
        'a': {
            'b': {
                'c': 'lol'
            },
            'x': 'internet'
        }
    }
    assert deep_get(['a', 'b', 'c'], dictionary) == 'lol'
    assert deep_get(['a', 'x'], dictionary) == 'internet'
    with pytest.raises(KeyError):
        deep_get(['a', 'z'], dictionary)


@pytest.mark.pybrew
def test_deep_set():
    dictionary1 = {
        'a': {
            'b': {
                'c': 'lol'
            },
            'x': 'internet'
        }
    }
    dictionary2 = {
        'a': {
            'b': {
                'c': 'lol2'
            },
            'x': 'internet'
        }
    }
    assert deep_set(['a', 'b', 'c'], 'lol2', dictionary1) == dictionary2


@pytest.mark.pybrew
def test_deep_transform():
    dictionary1 = {
        'a': {
            'b': {
                'c': [1, 2, 3]
            },
            'x': 'internet'
        }
    }
    dictionary2 = {
        'a': {
            'b': {
                'c': [2, 3, 4]
            },
            'x': 'internet'
        }
    }

    f = comp(list, map(lambda x: x + 1))

    assert deep_transform(['a', 'b', 'c'], f, dictionary1) == dictionary2
    assert deep_transform(['a', 'z'], f, dictionary1) == dictionary1


@pytest.mark.slow
@pytest.mark.pybrew
def test_labels_io(ORGANIZATION, TEST_REPOSITORY):
    assert 'documentation' in [
        x['name'] for x in labels_io(
            github_token=secret_io('GITHUB_WEBSITE_TOKEN'),
            organization=ORGANIZATION,
            repo_name=TEST_REPOSITORY
        )
    ]


@pytest.mark.slow
@pytest.mark.pybrew
def test_pull_requests_io(ORGANIZATION, TEST_REPOSITORY):
    results = [
        {
            "node": {
                "id": "MDExOlB1bGxSZXF1ZXN0MzY5OTkxMDA1",
                "number": 1,
                "state": "OPEN",
                "headRefName": "pull_request_test",
                "baseRefName": "master",
                "repository": {
                    "name": "website",
                    "owner": {
                        "login": "flowbrew"
                    }
                },
                "title": "Create TEST_FILE_FOR_PR.md",
                "mergeStateStatus": "UNSTABLE",
                "commits": {
                    "nodes": [
                        {
                            "commit": {
                                "pushedDate": s2t("2020-02-02T09:47:34Z"),
                                "oid": "062c33faed0a0195f204c2b494ecd3fef73238ff"
                            }
                        }
                    ]
                },
                "timelineItems": {
                    "nodes": [
                        {
                            "label": {
                                "name": "good first issue"
                            },
                            "createdAt": s2t("2020-02-02T09:26:10Z")
                        },
                        {
                            "label": {
                                "name": "good first issue"
                            },
                            "removedAt": s2t("2020-02-02T09:26:33Z")
                        },
                        {
                            "label": {
                                "name": "documentation"
                            },
                            "createdAt": s2t("2020-02-02T09:26:33Z")
                        },
                        {
                            "label": {
                                "name": "good first issue"
                            },
                            "createdAt": s2t("2020-02-02T09:26:47Z")
                        },
                        {
                            "label": {
                                "name": "duplicate"
                            },
                            "createdAt": s2t("2020-02-02T09:33:06Z")
                        },
                        {
                            "label": {
                                "name": "duplicate"
                            },
                            "removedAt": s2t("2020-02-02T09:33:19Z")
                        },
                        {
                            "label": {
                                "name": "bug"
                            },
                            "createdAt": s2t("2020-02-02T10:53:00Z")
                        }
                    ]
                }
            }
        }
    ]
    assert pull_requests_io(
        github_token=secret_io('GITHUB_WEBSITE_TOKEN'),
        organization=ORGANIZATION,
        repo_name=TEST_REPOSITORY
    ) == results


@pytest.mark.pybrew
def test_is_green_pull_request():
    assert not is_green_pull_request({
        "mergeStateStatus": "asgds",
    })
    assert is_green_pull_request({
        "mergeStateStatus": "CLEAN",
    })


@pytest.mark.pybrew
def test_is_staled_pull_request():
    current_time = s2t("2020-02-02T09:26:33Z")
    assert not is_stale_pull_request(current_time, {})
    assert not is_stale_pull_request(current_time, {
        "timelineItems": {
            "nodes": [
                {
                    "label": {
                        "name": split_test_label()
                    },
                    "createdAt": s2t("2020-02-02T09:26:10Z")
                },
                {
                    "label": {
                        "name": split_test_label()
                    },
                    "removedAt": s2t("2020-02-02T09:26:20Z")
                },
            ]
        }
    })
    assert not is_stale_pull_request(current_time, {
        "timelineItems": {
            "nodes": [
                {
                    "label": {
                        "name": split_test_label()
                    },
                    "createdAt": (
                        current_time - split_test_stale() + tdlt(seconds=1)
                    )
                },
            ]
        }
    })
    assert is_stale_pull_request(current_time, {
        "timelineItems": {
            "nodes": [
                {
                    "label": {
                        "name": split_test_label()
                    },
                    "createdAt": (
                        current_time - split_test_stale()
                    )
                },
            ]
        }
    })


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

import pytest
import tempfile
import os
from datetime import datetime
from path import Path
from pybrew import my_fun, notification_io, run_io, pipe, map, comp, force, try_n_times_decorator, tmp, extract_repo_name_from_origin, dict_to_filesystem_io, filesystem_to_dict_io, copy_dir_io, wait_until_html_deployed_io, allocate_traffic_to_pull_requests, extract_key, pull_requests_io, secret_io, is_green_pull_request, is_stale_pull_request, split_test_label, s2t, tdlt, t2s, split_test_stale, deep_get, deep_set, deep_transform, labels_io, build_test_deploy_check_name, partition, foldl, repeat, repository_io, url_join, job_name_to_workflow_id_io, pre_split_test_check_name


@pytest.mark.pybrew
def test_url_join():
    assert url_join('http://127.0.0.1:4000/', 'something') == \
        'http://127.0.0.1:4000/something'

    assert url_join('http://127.0.0.1:4000/', 'something', 'lol') == \
        'http://127.0.0.1:4000/something/lol'

    assert url_join('http://127.0.0.1:4000', 'something', 'lol') == \
        'http://127.0.0.1:4000/something/lol'

    assert url_join('http://127.0.0.1:4000', '', 'lol') == \
        'http://127.0.0.1:4000/lol'

    assert url_join('http://127.0.0.1:4000', None, 'lol') == \
        'http://127.0.0.1:4000/lol'

    assert url_join('http://127.0.0.1:4000', 'something/', '/lol') == \
        'http://127.0.0.1:4000/something/lol'

    assert url_join('http://127.0.0.1:4000/', '/something/', '/lol') == \
        'http://127.0.0.1:4000/something/lol'

    assert url_join('http://127.0.0.1:4000') == \
        'http://127.0.0.1:4000'

    assert url_join('http://127.0.0.1:4000/') == \
        'http://127.0.0.1:4000'

    assert url_join('http://127.0.0.1:4000', 'some/thing/', '/lol/') == \
        'http://127.0.0.1:4000/some/thing/lol'

    assert url_join('http://127.0.0.1:4000', 'some/thing/', '/lol?p=1') == \
        'http://127.0.0.1:4000/some/thing/lol?p=1'

    assert url_join('http://127.0.0.1:4000', 'some/thing/', '/lol', '?p=1') == \
        'http://127.0.0.1:4000/some/thing/lol?p=1'

    assert url_join('http://127.0.0.1:4000', '/lol.jpg', '?p=1') == \
        'http://127.0.0.1:4000/lol.jpg?p=1'

    assert url_join('http://127.0.0.1:4000', '/lol.jpg?p=1') == \
        'http://127.0.0.1:4000/lol.jpg?p=1'

    assert url_join('http://127.0.0.1:4000/', 'something.html') == \
        'http://127.0.0.1:4000/something.html'

    assert url_join('http://127.0.0.1:4000/', '/something.jpg') == \
        'http://127.0.0.1:4000/something.jpg'


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


@pytest.mark.pybrew
def test_allocate_traffic_to_pull_requests():
    def _pr(branch, state, time, checks):
        _checks = {
            "nodes": [
                {
                    "checkRuns": {
                        "nodes": []
                    }
                },
                {
                    "checkRuns": {
                        "nodes": checks
                    }
                },
                {
                    "checkRuns": {
                        "nodes": []
                    }
                },
            ]
        }
        return {
            "node": {
                "state": state,
                "headRefName": branch,
                "commits": {
                    "nodes": [
                        {
                            "commit": {
                                "pushedDate": time,
                                "checkSuites": _checks
                            }
                        }
                    ]
                }
            }
        }
    def _cheks(chk1, chk2):
        return [
            {
                "status": "COMPLETED",
                "conclusion": "SUCCESS" if chk1 else "FAILURE",
                "name": build_test_deploy_check_name()
            },
            {
                "status": "COMPLETED",
                "conclusion": "SUCCESS" if chk1 else "FAILURE",
                "name": pre_split_test_check_name()
            },
            {
                "status": "COMPLETED",
                "conclusion": "SUCCESS" if chk2 else "FAILURE",
                "name": "nothing"
            }
        ]
    pr1 = _pr(
        'test1',
        'OPEN',
        datetime.utcnow() + tdlt(seconds=1),
        _cheks(False, True)
    )
    pr2 = _pr(
        'test2',
        'CLOSED',
        datetime.utcnow() + tdlt(seconds=2),
        _cheks(True, False)
    )
    pr3 = _pr(
        'test3',
        'OPEN',
        datetime.utcnow() + tdlt(days=1),
        _cheks(True, False)
    )
    pr4 = _pr(
        'test4',
        'OPEN',
        datetime.utcnow() - tdlt(days=1),
        _cheks(True, False)
    )

    prs = [pr1, pr2, pr3, pr4]

    tests = [
        (0, [],         [pr4, pr1, pr2, pr3]),
        (1, [pr4],      [pr1, pr2, pr3]),
        (2, [pr4, pr3], [pr1, pr2]),
        (3, [pr4, pr3], [pr1, pr2]),
        (4, [pr4, pr3], [pr1, pr2]),
    ]

    for max_parallel_split_tests, r_yes, r_no in tests:
        yes, no = allocate_traffic_to_pull_requests(
            max_parallel_split_tests,
            prs
        )
        for x in no:
            print(x['node']['headRefName'])
        assert yes == r_yes
        assert no == r_no


@pytest.mark.slow
@pytest.mark.pybrew
def test_repository_io(ORGANIZATION, TEST_REPOSITORY):
    assert repository_io(
        github_token=secret_io('GITHUB_WEBSITE_TOKEN'),
        organization=ORGANIZATION,
        repo_name=TEST_REPOSITORY
    )['id'] == 'MDEwOlJlcG9zaXRvcnkyMzUzMzI5MDk='


@pytest.mark.slow
@pytest.mark.pybrew
def test_pull_requests_io(ORGANIZATION, TEST_REPOSITORY):
    results = {
        "node": {
            "id": "MDExOlB1bGxSZXF1ZXN0MzY5OTkxMDA1",
            "labels": {
                "edges": [
                    {"node": {"name": "bug"}},
                    {"node": {"name": "documentation"}},
                    {"node": {"name": "good first issue"}}
                    ]
            },
            "number": 1,
            "state": "OPEN",
            "headRefName": "pull_request_test",
            "baseRefName": "master",
            "repository": {
                "id": "MDEwOlJlcG9zaXRvcnkyMzUzMzI5MDk=",
                "name": "test-website-deployment",
                "owner": {
                        "login": "flowbrew"
                }
            },
            "title": "Create TEST_FILE_FOR_PR.md",
            "mergeStateStatus": "NOT_IMPORTANT",
            "commits": {
                "nodes": [
                    {
                        "commit": {
                                "pushedDate": s2t("2020-02-02T09:47:34Z"),
                                "oid": "062c33faed0a0195f204c2b494ecd3fef73238ff",
                                "checkSuites": {
                                    "nodes": [
                                        {
                                            "databaseId": 433375438,
                                            "checkRuns": {
                                                "nodes": []
                                            }
                                        },
                                        {
                                            "databaseId": 433375451,
                                            "checkRuns": {
                                                "nodes": [
                                                    {
                                                        "status": "COMPLETED",
                                                        "conclusion": "FAILURE",
                                                        "name": "nothing-error"
                                                    },
                                                    {
                                                        "status": "COMPLETED",
                                                        "conclusion": "SUCCESS",
                                                        "name": "nothing"
                                                    }
                                                ]
                                            }
                                        }
                                    ]
                                }
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
    r = pull_requests_io(
        github_token=secret_io('GITHUB_WEBSITE_TOKEN'),
        organization=ORGANIZATION,
        repo_name=TEST_REPOSITORY
    )[0]
    r1 = deep_set(['node', 'mergeStateStatus'], "NOT_IMPORTANT", r)
    assert r1 == results

    assert job_name_to_workflow_id_io(r1, 'nothing-error') == 433375451


@pytest.mark.pybrew
def test_is_green_pull_request():
    assert not is_green_pull_request({
        "node": {
            "mergeStateStatus": "asgds",
        }
    })
    assert is_green_pull_request({
        "node": {
            "mergeStateStatus": "CLEAN",
        }
    })


@pytest.mark.pybrew
def test_is_staled_pull_request():
    current_time = s2t("2020-02-02T09:26:33Z")
    assert not is_stale_pull_request(current_time, {})
    assert not is_stale_pull_request(current_time, {
        "node": {
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
        }
    })
    assert not is_stale_pull_request(current_time, {
        "node": {
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
        }
    })
    assert is_stale_pull_request(current_time, {
        "node": {
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

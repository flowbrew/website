import pytest
import tempfile
import os
from path import Path
from pybrew import my_fun, notification_io, run_io, pipe, map, comp, force, b2p, tmp, applyw, inject_branch_to_deployment, dict_to_filesystem_io, filesystem_to_dict_io, random_str, deploy_to_github_io, http_get_io, delete_github_repo_io, branch_to_prefix, try_n_times_decorator, remove_branch_from_deployment, remove_from_github_io, wait_until_deployed_by_sha_io


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


@pytest.mark.slow
def test_deploy_to_github_io(
    SECRET_GITHUB_WEBSITE_USERNAME,
    SECRET_GITHUB_WEBSITE_TOKEN,
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
                username=SECRET_GITHUB_WEBSITE_USERNAME,
                token=SECRET_GITHUB_WEBSITE_TOKEN,
                organization=ORGANIZATION,
                repo_name=TEST_REPOSITORY,
                branch=br,
                path=td
            )

    wait_until_deployed_by_sha_io(
        'https://' + ORGANIZATION + '.github.io/' +
        TEST_REPOSITORY + '/' + p1_.replace('.html', ''),
        SHA
    )

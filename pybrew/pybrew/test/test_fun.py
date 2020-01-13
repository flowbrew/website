import pytest
import tempfile
import os
from path import Path
from pybrew import my_fun, notification, run, pipe, map, comp, force


def test_my_fun():
    assert my_fun(4) == 5


def test_notification(SLACK_BOT_TOKEN):
    assert notification(
        channel='#test',
        text='Hello World',
        token=SLACK_BOT_TOKEN
    )


def test_run():
    assert run('echo hello').startswith('hello')
    with pytest.raises(Exception):
        run('echo23423 hello')


def master():
    return 'master'


def branch_suffix():
    return 'branch_'


def branch_folder(branch):
    if branch == master():
        return branch
    return branch_suffix() + branch


class FilesystemDeployProvider:
    @staticmethod
    def _repo_to_path(dest_repo):
        return os.path.join('./', dest_repo)

    @staticmethod
    def config(name, email):
        pass

    @staticmethod
    def create_repo_if_not_exists(dest_repo):
        path = FilesystemDeployProvider._repo_to_path(dest_repo)
        if not os.path.isdir(path):
            run(f'mkdir -p {path}')

    @staticmethod
    def clone(website_path, dest_repo):
        with Path(website_path):
            pass

    @staticmethod
    def remove(website_path, pattern):
        with Path(website_path):
            pass

    @staticmethod
    def copy(source_path, dest_path):
        pass

    @staticmethod
    def push(website_path):
        with Path(website_path):
            pass


def deploy(dp, source_path, branch, dest_repo):
    dp.config()
    dp.create_repo_if_not_exists(dest_repo)

    with tempfile.TemporaryDirectory() as website_path:
        new_branch_path = os.path.join(
            website_path, branch_folder(branch)
        )
        master_branch_path = os.path.join(
            website_path, branch_folder(master())
        )

        dp.clone(website_path, dest_repo)
        dp.remove(website_path, f'^(?!{branch_suffix()}.*)$')
        dp.remove(website_path, f'^({branch_folder(branch)})$')

        dp.copy(source_path, new_branch_path)
        dp.copy(master_branch_path, website_path)

        dp.push(website_path)


def test_parallel_branching_deployment(
    SECRET_SLACK_BOT_TOKEN,
    SECRET_GITHUB_WEBSITE_USERNAME,
    SECRET_GITHUB_WEBSITE_TOKEN,
    tmp_path
):
    # domain = ''
    branches = ['a', 'b', 'master']

    def branch_content(data):
        return pipe(
            ['1.html', '2.html', '3.html'],
            map(lambda x: run(f'echo {data} > {x}'))
        )

    def website_content(payload):
        def proc(branch):
            run(f'mkdir ./{branch}')
            with Path(f'./{branch}'):
                return payload(branch)

        return map(proc, branches)

    def make_and_deploy(branch):
        with tempfile.TemporaryDirectory() as wd:
            with Path(wd):
                force(website_content(lambda _: branch_content(branch)))
                deploy(
                    FilesystemDeployProvider(), 
                    source_path='./', 
                    branch=branch,
                    dest_repo='flowbrew/website-deployment'
                    )

    map(make_and_deploy, branches)

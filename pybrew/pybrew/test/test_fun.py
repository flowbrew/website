import pytest
import tempfile
import os
import glob
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


def remove_from(wd, pattern):
    for p in Path(wd).glob(pattern):
        p.unlink()

def copy_from(from_path, to_path):
    run(f'mkdir -p {to_path}')
    run(f'cp -r {from_path}/. {to_path}')

class FilesystemDeployProvider:
    @staticmethod
    def _repo_to_path(repo):
        return os.path.join('/repos/', repo)

    @staticmethod
    def config(name, email):
        pass

    @staticmethod
    def create_repo_if_not_exists(repo):
        repo_path = FilesystemDeployProvider._repo_to_path(repo)
        if not os.path.isdir(repo_path):
            run(f'mkdir -p {repo_path}')

    @staticmethod
    def clone(wd, repo):
        repo_path = FilesystemDeployProvider._repo_to_path(repo)
        copy_from(repo_path, wd)

    @staticmethod
    def push(wd, repo):
        repo_path = FilesystemDeployProvider._repo_to_path(repo)
        copy_from(wd, repo_path)


def deploy(dp, source_path, branch, repo):
    dp.config() # IO
    dp.create_repo_if_not_exists(repo) # IO

    with tempfile.TemporaryDirectory() as wd: # IO
        new_branch_path = os.path.join(wd, branch_folder(branch))
        master_branch_path = os.path.join(wd, branch_folder(master()))

        dp.clone(wd, repo) # IO

        dp.remove_from(wd, f'!(/{branch_suffix()}*)') # IO
        dp.remove_from(wd, f'/{branch_folder(branch)}/*') # IO

        dp.copy_from(source_path, new_branch_path) # IO
        dp.copy_from(master_branch_path, wd) # IO

        dp.push(wd, repo) # IO


def test_remove_from(tmp_path):
    with Path(tmp_path):
        run('mkdir ./test')
        run('echo 123 > ./test/123.txt')

        run('mkdir ./lol')
        run('echo 123 > ./lol/test.txt')

        run('mkdir ./nn')
        run('echo 123 > ./nn/test.txt')

        run('mkdir ./test2')
        run('echo 123 > ./test2/123.txt')

    remove_from(tmp_path, '!(/test*)')

    assert Path('./test/123.txt').read_text() == '123'
    assert Path('./test2/123.txt').read_text() == '123'

def test_copy_from(tmp_path):
    (tmp_path / 'a').mkdir()
    (tmp_path / 'b').mkdir()

    with Path(tmp_path / 'a'):
        run('mkdir ./test')
        run('echo 123 > ./test/123.txt')

        run('mkdir ./lol')
        run('echo 123 > ./lol/test.txt')

    copy_from(tmp_path / 'a', tmp_path / 'b')

    assert (tmp_path / 'b/test/123.txt').read_text() == '123'
    assert (tmp_path / 'b/lol/test.txt').read_text() == '123'

def test_branching_deployment(
    SECRET_SLACK_BOT_TOKEN,
    SECRET_GITHUB_WEBSITE_USERNAME,
    SECRET_GITHUB_WEBSITE_TOKEN,
    tmp_path
):
    branches = ['a', 'b', 'master']

    def init_source_here(branch):
        def init_branch_content():
            return pipe(
                ['1.html', '2.html', '3.html'],
                map(lambda x: run(f'echo {branch} > {x}'))
            )

        def init_branches_content(local_branch_path):
            run(f'mkdir {local_branch_path}')
            with Path(local_branch_path):
                return init_branch_content()

        return pipe(
            branches,
            map(comp(lambda x: f'./{x}', branch_folder)),
            map(init_branches_content)
        )

    def make_and_deploy(branch):
        with tempfile.TemporaryDirectory() as source_dir:
            with Path(source_dir):
                comp(force, init_source_here)(branch)
            deploy(
                FilesystemDeployProvider(),
                source_path=source_dir,
                branch=branch,
                repo='flowbrew/website-deployment'
            )

    comp(force, map)(make_and_deploy, branches)



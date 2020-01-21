import os
import slack
import shlex
import pytest
from subprocess import check_output, CalledProcessError
import random
import string
import tempfile
import requests
import time
import yaml

from bs4 import BeautifulSoup
from path import Path

from toolz import compose, curry, pipe
from toolz.curried import map
from toolz.itertoolz import get
from functools import partial

from fn.iters import flatten
from itertools import chain


def chain_(x): return chain(*x)


apply = curry(lambda f, x: f(x))
applyw = curry(lambda f, x: f(*x))


def flip(f): return lambda *a: f(*reversed(a))


apply_ = flip(apply)
comp = compose
comp_ = flip(compose)
flip = comp(curry, flip)


def nt(x): return not (x)


filter = curry(filter)
get = curry(get)


def try_n_times_decorator(n=5, timeout=5):
    def helper1(f):
        def helper2(*args, **kwargs):
            for i in range(n):
                try:
                    return f(*args, **kwargs)
                except:
                    if i >= n - 1:
                        raise
                    time.sleep(timeout)
        return helper2
    return helper1


def bottom(x):
    pass


force = compose(any, map(bottom))


def my_fun(x):
    return x + 1


def master_branch() -> str:
    return 'master'


def branch_prefix() -> str:
    return 'branch_'


def branch_to_prefix(branch: str) -> str:
    return branch_prefix() + branch + '/'


def add_prefix(branch: str, x: str) -> str:
    return branch_to_prefix(branch) + x


def remove_prefix(x: str) -> str:
    return x.split('/', 1)[1]


b2p = branch_to_prefix


def files(path):
    for r, _, fs in os.walk(path):
        for f in fs:
            yield os.path.join(r, f)


# def run(command_line):
#     print('>', command_line)
#     result = check_output(shlex.split(command_line)).decode("utf-8")
#     print(result)
#     return result


def run_io(command_line):
    if os.system(command_line):
        raise Exception(f'Exception while executing "{command_line}"')


def notification_io(channel, text, token):
    client = slack.WebClient(token)
    response = client.chat_postMessage(
        channel=channel,
        text=text
    )
    return response["ok"]


startswith_ = flip(str.startswith)
is_any_branch = comp(startswith_, branch_prefix)()
is_specific_branch = comp(startswith_, b2p)
is_git = startswith_('.git')
is_master_branch = is_specific_branch(master_branch())


def clean_deployment_state(state: dict, branch_to_delete: str):
    is_target_branch = is_specific_branch(branch_to_delete)
    return {
        k: v
        for k, v in state.items()
        if (is_any_branch(k) and not is_target_branch(k)) or is_git(k)
    }


def extract_master_state(state: dict):
    return {
        remove_prefix(k): v
        for k, v in state.items()
        if is_master_branch(k)
    }


def remove_branch_from_deployment(
    branch_name: str,
    deployment_state: dict,
) -> dict:
    cleaned_deployment_state = clean_deployment_state(
        deployment_state, branch_name
    )

    return {
        **cleaned_deployment_state,
        **extract_master_state(cleaned_deployment_state)
    }


def inject_branch_to_deployment(
    branch_name: str,
    branch_state: dict,
    deployment_state: dict,
) -> dict:
    cleaned_deployment_state = clean_deployment_state(
        deployment_state, branch_name
    )

    branch_state_ = {
        add_prefix(branch_name, k): v
        for k, v in branch_state.items()
    }

    injected_state = {
        **cleaned_deployment_state,
        **branch_state_
    }

    return {
        **injected_state,
        **extract_master_state(injected_state)
    }


def filesystem_to_dict_io(path: str) -> dict:
    def clean_key(path, key):
        return key.replace(path, '', 1).strip('/')

    def extract_data_io(path):
        for dirpath, dirs, files in os.walk(path):
            if not dirs and not files:
                yield (clean_key(path, dirpath), None)
            else:
                for x in files:
                    key = os.path.join(dirpath, x)
                    with open(key, 'rb') as f:
                        yield (clean_key(path, key), f.read())

    return pipe(
        extract_data_io(path),
        dict
    )


def dict_to_filesystem_io(mount_path: str, data: dict) -> str:
    def kv_to_filesystem_io(file_path, file_data):
        if file_data is None:
            os.makedirs(file_path, exist_ok=True)
            return
        tail, _ = os.path.split(file_path)
        os.makedirs(tail, exist_ok=True)
        with open(file_path, 'wb') as f:
            t = type(file_data)
            if t == str:
                f.write(file_data.encode('utf-8'))
            elif t == bytes:
                f.write(file_data)
            else:
                raise Exception(
                    'Dont know how to write {file_path} to filesystem'
                )

    force(
        kv_to_filesystem_io(os.path.join(mount_path, k), v)
        for k, v in data.items()
    )


def random_str(size=16, chars=string.ascii_lowercase):
    return ''.join(random.choice(chars) for x in range(size))


def http_get_io(url):
    print('get', url)
    s = requests.session()
    headers = {
        'User-Agent': 'Github Action',
        'Cache-Control': 'no-cache'
    }
    r = s.get(url, headers=headers).text
    s.cookies.clear()
    return r


tmp = tempfile.TemporaryDirectory


def github_endpoint():
    return 'https://api.github.com'


def github_enable_pages_site_io(
    username: str,
    token: str,
    organization: str,
    repo_name: str,
    branch: str = 'master',
    path: str = ''
):
    url = f"{github_endpoint()}/repos/{organization}/{repo_name}/pages"
    headers = {'Accept': 'application/vnd.github.switcheroo-preview+json'}
    content = {
        "source": {
            "branch": branch,
            "path": path,
            "auto_init": True
        }
    }
    r = requests.post(
        url,
        json=content,
        headers=headers,
        auth=(username, token)
    ).json()
    print(r)
    return r


def github_create_repo_io(
    username: str,
    token: str,
    organization: str,
    repo_name: str,
):
    url = f"{github_endpoint()}/orgs/{organization}/repos"
    content = {
        "name": repo_name,
        "private": False,
    }
    r = requests.post(url, json=content, auth=(username, token)).json()
    return r


def github_delete_repo_io(
    username: str,
    token: str,
    organization: str,
    repo_name: str,
):
    url = f"{github_endpoint()}/repos/{organization}/{repo_name}"
    requests.delete(url, auth=(username, token))


def github_clone_url(
    username: str,
    token: str,
    organization: str,
    repo_name: str,
):
    return (
        'https://' + username + ':' + token + '@github.com/' +
        organization + '/' + repo_name + '.git'
    )


def validate_github_operation(
    username: str,
    token: str,
    organization: str,
    repo_name: str,
):
    if not username or not token:
        raise Exception('Empty credential')


def github_push_io(path, message):
    with Path(path):
        run_io(f'git add --all')
        run_io(f'git commit --allow-empty -m "{message}"')
        run_io(f'git push')


def github_clone_io(username, token, organization, repo_name, path):
    clone_url = github_clone_url(username, token, organization, repo_name)
    run_io(f'git clone {clone_url} {path}')


def github_modify_io(
    username: str,
    token: str,
    organization: str,
    repo_name: str,
    message: str,
    f
):
    with tmp() as repo_path, tmp() as new_repo_path:
        github_clone_io(username, token, organization, repo_name, repo_path)
        f(repo_path, new_repo_path)
        github_push_io(new_repo_path, message)


@try_n_times_decorator(n=5, timeout=10)
def deploy_to_github_io(
    github_username: str,
    github_token: str,
    organization: str,
    repo_name: str,
    branch: str,
    path: str,
):
    params = [username, token, organization, repo_name]

    validate_github_operation(*params)

    github_create_repo_io(*params)
    github_enable_pages_site_io(*params)

    def _modify(repo_path, new_repo_path):
        dict_to_filesystem_io(
            new_repo_path,
            inject_branch_to_deployment(
                branch,
                filesystem_to_dict_io(path),
                filesystem_to_dict_io(repo_path)
            )
        )

    github_modify_io(*params, f'Updated branch {branch}', _modify)


@try_n_times_decorator(n=5, timeout=10)
def remove_from_github_io(
    username: str,
    token: str,
    organization: str,
    repo_name: str,
    branch: str,
):
    params = [username, token, organization, repo_name]

    validate_github_operation(*params)

    def _modify(repo_path, new_repo_path):
        dict_to_filesystem_io(
            new_repo_path,
            remove_branch_from_deployment(
                branch,
                filesystem_to_dict_io(repo_path)
            )
        )

    github_modify_io(*params, f'Deleted branch {branch}', _modify)


def delete_github_repo_io(
    username: str,
    token: str,
    organization: str,
    repo_name: str,
):
    params = [username, token, organization, repo_name]
    validate_github_operation(*params)
    github_delete_repo_io(*params)


def url_(domain: str, branch: str, path: str):
    return f'https://{domain}/{branch}/{path}'


def wait_until_deployed_by_sha_io(url: str, sha: str):
    wait_until_html_deployed_io(
        url,
        lambda soup:
        soup.find('meta', {'name': 'github-commit-sha'}).get('content') == sha
    )


def wait_until_deployed_by_sha_io_(domain, branch, sha):
    wait_until_deployed_by_sha_io(
        'https://' + domain + '/' + branch_to_prefix(branch),
        sha
    )


@try_n_times_decorator(n=20, timeout=20)
def wait_until_html_deployed_io(url: str, f):
    html = http_get_io(url)
    soup = BeautifulSoup(html, features="html.parser")
    if not f(soup):
        raise Exception(f'Invalid html {url}')


def load_yaml_io(path):
    with open(path, 'r') as file:
        return yaml.safe_load(file)


def save_yaml_io(path, data):
    with open(path, 'w') as file:
        yaml.safe_dump(data, file)


def build_jekyll_io(repo_path: str, dest: str, sha: str, branch: str):
    with Path(repo_path):
        save_yaml_io(
            '_config.yml',
            {
                **load_yaml_io('_config.yml'),
                **{
                    'baseurl': (
                        '/' if branch == master_branch()
                        else branch_to_prefix(branch)
                    ),
                    'github-branch': branch,
                    'github-commit-sha': sha,
                    'no-index': branch != master_branch(),
                }
            }
        )

        run_io(f'jekyll build --trace -d {dest}')


def domain_io(path):
    with open('CNAME', 'r') as f:
        return f.read().strip('\r\n').strip()


def github_action_notification_io(
    slack_token: str,
    workflow: str,
    repo_name: str,
    branch: str,
    event_name: str,
    head_commit_message: str,
    head_commit_url: str,
    success: bool,
):
    where_str = f"{workflow} of {repo_name}, branch '{branch}'"

    what_str = f"{'SUCCESS ✅' if success else 'FAILURE ❌'} on event '{event_name}'"

    last_commit_str = (
        f"Last commit was '{head_commit_message}'\n{head_commit_url}"
        if head_commit_message else
        ''
    )

    text = f'{what_str} on {where_str}\n{last_commit_str}\n---'

    notification_io(channel='#website', text=text, token=slack_token)


def test_pybrew_io(
    github_username,
    github_token,
    slack_token,
    sha,
    branch,
    test_repo_name,
    organization,
):
    run_io(f'''
        pytest -vv --color=yes --pyargs pybrew \
            --runslow \
            --SECRET_GITHUB_WEBSITE_USERNAME={github_username} \
            --SECRET_GITHUB_WEBSITE_TOKEN={github_token} \
            --SECRET_SLACK_BOT_TOKEN={slack_token} \
            --SHA={sha} \
            --BRANCH={branch} \
            --TEST_REPOSITORY={test_repo_name} \
            --ORGANIZATION={organization}
        ''')


def cicd_io(**kwargs):
    notify_io_ = partial(github_action_notification_io, **kwargs)

    try:
        test_pybrew_io(**kwargs)

        with tmp() as website:
            build_jekyll_io(dest=website, **kwargs)
            deploy_to_github_io(path=website, **kwargs)
            wait_until_deployed_by_sha_io_(
                domain=domain_io(website),
                **kwargs
            )

        notify_io_(success=True)

    except:
        notify_io_(success=False)
        raise

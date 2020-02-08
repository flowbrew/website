import os
import slack
import shlex
import pytest
from subprocess import check_output, CalledProcessError, run as srun
import random
import string
import tempfile
import requests
import time
import yaml
import re
import shutil
import more_itertools
from collections import Counter
from datetime import datetime, timedelta

from bs4 import BeautifulSoup
from path import Path

from toolz import compose, curry, pipe
from toolz.curried import map
from toolz.itertoolz import get
from toolz.functoolz import identity
from functools import partial, reduce as reduce_, lru_cache

from fn.iters import flatten
from itertools import chain, product, tee, filterfalse, repeat

from cachier import cachier
from contextlib import contextmanager

import boto3


def chain_(x): return chain(*x)


apply = curry(lambda f, x: f(x))
applyw = curry(lambda f, x: f(*x))
product = curry(product)


@curry
def reduce(f, initializer, iterable):
    return reduce_(f, iterable, initializer)


def flip(f): return lambda *a: f(*reversed(a))


apply_ = flip(apply)
comp = compose
comp_ = flip(compose)
flip = comp(curry, flip)

filter = curry(filter)
filterempty = filter(identity)
foldl = reduce


def nt(x): return not (x)


filter = curry(filter)
get = curry(get)


def frequency(data):
    return dict(Counter(data))


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


def url_join(*args_):
    args = [x for x in args_ if x]

    assert ''.join(args).count('?') <= 1
    assert ''.join(args).count('?') == 0 or '?' in args[-1]

    a1, params = partition(lambda x: '?' not in x, args)

    if params:
        a, params2_ = params[0].split('?')
        params2 = '?' + params2_
    else:
        a, params2 = ('', '')

    a2 = [x.strip('/') for x in a1 + [a] if x]

    return '/'.join(a2) + params2


def split_test_label() -> str:
    return 'SPLIT TESTING'


def split_test_stale():
    return tdlt(days=5)


def master_branch() -> str:
    return 'master'


def branch_prefix() -> str:
    return 'branch_'


def build_test_deploy_check_name() -> str:
    return 'build-test-deploy'


def branch_to_prefix(branch: str) -> str:
    return branch_prefix() + branch + '/'


def add_prefix(branch: str, x: str) -> str:
    return branch_to_prefix(branch) + x


def remove_prefix(x: str) -> str:
    return x.split('/', 1)[1]


b2p = branch_to_prefix


def files_io(path):
    for r, _, fs in os.walk(path):
        for f in fs:
            yield os.path.join(r, f)


def run_io(command_line_):
    command_line = command_line_.replace('\n', ' ').strip('\n').strip()
    print('>', command_line)
    srun(command_line, shell=True, check=True)


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


def filesystem_to_dict_io(path: str, index_only: bool = False) -> dict:
    def clean_key(path, key):
        return key.replace(path, '', 1).strip('/')

    def extract_data_io(path):
        for dirpath, dirs, files in os.walk(path):
            if not dirs and not files:
                yield (clean_key(path, dirpath), None)
            else:
                for x in files:
                    key = os.path.join(dirpath, x)
                    if index_only:
                        yield (clean_key(path, key), '')
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


def extract_key(d, key):
    return ({k: v for k, v in d.items() if k != key}, d.get(key, None))


def random_str(size=16, chars=string.ascii_lowercase):
    return ''.join(random.choice(chars) for x in range(size))


def http_get_io(url):
    print('get', url)
    s = requests.session()
    headers = {
        'User-Agent': 'Github Action',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0',
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
    headers = {
        'Accept': 'application/vnd.github.switcheroo-preview+json'
    }
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


def git_has_unstaged_changes_io(path='.'):
    return check_output(['git', 'status', '-s', '-uall', path]) != b''


def github_push_io(path, message, allow_empty):
    with Path(path):
        if not allow_empty and not git_has_unstaged_changes_io():
            return False
        run_io(f'git add --all')
        run_io(f'git commit \
                    {"--allow-empty" if allow_empty else ""} \
                    -m "{message}"')
        run_io(f'git push')
        return True


def github_clone_io(username, token, organization, repo_name, branch, path):
    clone_url = github_clone_url(username, token, organization, repo_name)
    run_io(f'git clone \
                --depth 1 \
                --single-branch --branch "{branch}" \
                "{clone_url}" \
                "{path}"')


def github_modify_io(
    github_username: str,
    github_token: str,
    organization: str,
    repo_name: str,
    branch: str,
    message: str,
    allow_empty: bool,
    f
):
    with tmp() as repo_path, tmp() as new_repo_path:
        github_clone_io(
            github_username,
            github_token,
            organization,
            repo_name,
            branch,
            repo_path
        )
        f(repo_path, new_repo_path)
        return github_push_io(new_repo_path, message, allow_empty)


@try_n_times_decorator(n=5, timeout=10)
def deploy_to_github_io(
    github_username,
    github_token,
    organization,
    target_repo_name,
    branch,
    path,
    **kwargs
):
    params = [github_username, github_token, organization, target_repo_name]

    validate_github_operation(*params)

    github_create_repo_io(*params)
    github_enable_pages_site_io(*params)

    def _modify_io(repo_path, new_repo_path):
        dict_to_filesystem_io(
            new_repo_path,
            inject_branch_to_deployment(
                branch,
                filesystem_to_dict_io(path),
                filesystem_to_dict_io(repo_path)
            )
        )

    github_modify_io(
        github_username=github_username,
        github_token=github_token,
        organization=organization,
        repo_name=target_repo_name,
        branch='master',
        message=f'Updated branch {branch}',
        allow_empty=True,
        f=_modify_io
    )


@try_n_times_decorator(n=5, timeout=10)
def remove_from_github_io(
    github_username: str,
    github_token: str,
    organization: str,
    target_repo_name: str,
    target_branch_name: str,
    **kwargs
):
    params = [github_username, github_token, organization, target_repo_name]

    validate_github_operation(*params)

    def _modify_io(repo_path, new_repo_path):
        dict_to_filesystem_io(
            new_repo_path,
            remove_branch_from_deployment(
                target_branch_name,
                filesystem_to_dict_io(repo_path)
            )
        )

    github_modify_io(
        github_username=github_username,
        github_token=github_token,
        organization=organization,
        repo_name=target_repo_name,
        branch='master',
        message=f'Deleted branch {target_branch_name}',
        allow_empty=True,
        f=_modify_io
    )


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


@curry
def merge_pull_request_io(github_token, pull_request, mid=None):
    mid = random_str() if not mid else mid
    query = '''
    mutation ($mutation_id: String, $pull_request_id: ID!) {
        mergePullRequest(input: {
            clientMutationId: $mutation_id, 
            pullRequestId:  $pull_request_id,
            mergeMethod: SQUASH
        }) {
            clientMutationId
        }
    }
    '''
    return requests.post(
        'https://api.github.com/graphql',
        json={
            'query': query,
            'variables': {
                'mutation_id': mid,
                'pull_request_id': pull_request['node']['id']
            }
        },
        headers={
            'Authorization': 'token ' + github_token,
        }
    ).json()['data']['mergePullRequest']['clientMutationId']


@curry
def job_name_to_workflow_id_io(pull_request, job_name):
    checkSuites = deep_get(
        ['node', 'commits', 'nodes', 0, 'commit', 'checkSuites', 'nodes'],
        pull_request
    )

    return next(
        x for x in checkSuites if
        any(
            True for y in deep_get(['checkRuns', 'nodes'], x)
            if y['name'] == job_name
        )
    ).get('databaseId')


@curry
def workflow_runs_io(
    github_token,
    organization,
    repo_name,
    yml_file,
    branch,
    status=None
):
    url = github_endpoint() + \
        f"/repos/{organization}/{repo_name}/actions/workflows/{yml_file}.yml/runs?branch={branch}" + \
        ('' if not status else '&status=' + status)

    r = requests.get(
        url,
        headers={
            'Authorization': 'token ' + github_token,
        },
    )
    return r.json()['workflow_runs']


@curry
def re_run_workflow_io(github_token, pull_request, yml_file, status=None):
    branch = deep_get(['node', 'headRefName'], pull_request)
    sha = deep_get(
        ['node', 'commits', 'nodes', 0, 'commit', 'oid'],
        pull_request
    )
    repo_name = deep_get(['node', 'repository', 'name'], pull_request)
    organization = deep_get(
        ['node', 'repository', 'owner', 'login'],
        pull_request
    )

    try:
        workflow_id = next(
            x for x in workflow_runs_io(
                github_token,
                organization,
                repo_name,
                yml_file,
                branch,
                status=status
            ) if x['head_sha'] == sha and x['head_branch'] == branch
        )['id']
    except StopIteration:
        return

    url = github_endpoint() + \
        f"/repos/{organization}/{repo_name}/actions/runs/{workflow_id}/rerun"

    requests.post(
        url,
        headers={
            'Authorization': 'token ' + github_token,
        },
    )


@curry
def close_pull_request_io(github_token, pull_request, mid=None):
    mid = random_str() if not mid else mid
    query = '''
    mutation ($mutation_id: String, $pull_request_id: ID!) {
        closePullRequest(input: {
            clientMutationId: $mutation_id, 
            pullRequestId:  $pull_request_id
        }) {
            clientMutationId
        }
    }
    '''
    r = requests.post(
        'https://api.github.com/graphql',
        json={
            'query': query,
            'variables': {
                'mutation_id': mid,
                'pull_request_id': pull_request['node']['id']
            }
        },
        headers={
            'Authorization': 'token ' + github_token,
        }
    ).json()
    return r['data']['closePullRequest']['clientMutationId']


@curry
def _label_io(op, github_token, labelable_id, label_id, mid=None):
    mid = random_str() if not mid else mid
    query = '''
    mutation ($label_id: ID!, $labelable_id: ID!, $mutation_id: String) {
        %s(input: {
            clientMutationId: $mutation_id,
            labelableId: $labelable_id,
            labelIds: [$label_id]
        }) {
            clientMutationId
        }
    }
    ''' % op
    return requests.post(
        'https://api.github.com/graphql',
        json={
            'query': query,
            'variables': {
                'mutation_id': mid,
                'labelable_id': labelable_id,
                'label_id': label_id,
            }
        },
        headers={
            'Authorization': 'token ' + github_token,
        },
    ).json()['data'][op]['clientMutationId']


@curry
def create_split_test_label_io(github_token, repository_id):
    return create_label_io(
        github_token=github_token,
        repository_id=repository_id,
        name=split_test_label(),
        color='0075ca',
        description='The branch is receiving live traffic',
        mid=None
    )


@curry
def create_label_io(
    github_token,
    repository_id,
    name,
    color,
    description,
    mid=None
):
    mid = random_str() if not mid else mid
    query = '''
    mutation (
        $repositoryId: ID!, 
        $color: String!,
        $description: String,
        $name: String,
        $mutation_id: String
    ) {
        createLabel(input: {
            clientMutationId: $mutation_id,
            color: $color,
            description: $description,
            name: $name,
            repositoryId: $repositoryId,
        }) {
            clientMutationId
            label {
                id
            }
        }
    }
    '''
    return requests.post(
        'https://api.github.com/graphql',
        json={
            'query': query,
            'variables': {
                'mutation_id': mid,
                'color': color,
                'description': description,
                'name': name,
                'repositoryId': repository_id,
            }
        },
        headers={
            'Authorization': 'token ' + github_token,
            'Accept': 'application/vnd.github.bane-preview+json',
        },
    ).json()['data']['createLabel']['clientMutationId']


@curry
def _label_io_(op, label, github_token, pull_request):
    labels = labels_io(
        github_token=github_token,
        organization=pull_request['node']['repository']['owner']['login'],
        repo_name=pull_request['node']['repository']['name'],
    )

    return _label_io(
        op,
        github_token=github_token,
        labelable_id=pull_request['node']['id'],
        label_id=next(x['id'] for x in labels if x['name'] == label)
    )


remove_split_test_label_io = _label_io_(
    'removeLabelsFromLabelable',
    split_test_label()
)

add_split_test_label_io = _label_io_(
    'addLabelsToLabelable',
    split_test_label()
)


@curry
def deep_get(keys, dictionary):
    return reduce(
        lambda d, key: d[key],
        dictionary,
        keys
    )


deep_get_ = lambda *keys: deep_get(keys)


@curry
def deep_set(keys, value, dictionary):
    h, *t = keys

    return {
        **dictionary,
        **(
            {h: deep_set(t, value, dictionary[h])}
            if t else
            {h: value}
        )
    }


@curry
def deep_transform(keys, f, dictionary):
    try:
        v = deep_get(keys, dictionary)
    except KeyError:
        return dictionary
    return deep_set(
        keys,
        f(v),
        dictionary,
    )


@curry
def deep_map_f(keys, f, dictionary):
    return deep_transform(keys, comp(list, map(f)), dictionary)


@curry
def labels_io(github_token, organization, repo_name):
    query = '''
    query ($owner: String!, $name: String!){
        repository(owner: $owner, name: $name) {
            labels(last:100) {
                nodes {
                    id
                    name
                }
            }
        }
    }
    '''
    return requests.post(
        'https://api.github.com/graphql',
        json={
            'query': query,
            'variables': {
                'owner': organization,
                'name': repo_name,
            }
        },
        headers={
            'Authorization': 'token ' + github_token,
        }
    ).json()['data']['repository']['labels']['nodes']


@curry
def repository_io(github_token, organization, repo_name):
    query = '''
query ($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    id
  }
}
    '''
    return requests.post(
        'https://api.github.com/graphql',
        json={
            'query': query,
            'variables': {
                'owner': organization,
                'name': repo_name,
            }
        },
        headers={
            'Authorization': 'token ' + github_token,
        }
    ).json()['data']['repository']


@curry
def pull_requests_io(github_token, organization, repo_name):
    query = '''
query ($owner: String!, $name: String!, $master: String!) {
  repository(owner: $owner, name: $name) {
    pullRequests(last: 100, baseRefName: $master) {
      edges {
        node {
          id
          labels(last: 10) {
            edges {
              node {
                name
              }
            }
          }
          number
          state
          headRefName
          baseRefName
          title
          repository {
            id
            name
            owner {
              login
            }
          }
          mergeStateStatus
          commits(last: 1) {
            nodes {
              commit {
                pushedDate
                oid
                checkSuites(last: 10) {
                  nodes {
                    databaseId
                    checkRuns(last: 10) {
                      nodes {
                        status
                        conclusion
                        name
                      }
                    }
                  }
                }
              }
            }
          }
          timelineItems(last: 100, itemTypes: [LABELED_EVENT, UNLABELED_EVENT]) {
            nodes {
              ... on LabeledEvent {
                label {
                  name
                }
                createdAt
              }
              ... on UnlabeledEvent {
                label {
                  name
                }
                removedAt: createdAt
              }
            }
          }
        }
      }
    }
  }
}
    '''
    transform_pr = comp_(
        deep_map_f(
            ['node', 'commits', 'nodes'],
            deep_transform(['commit', 'pushedDate'], s2t),
        ),
        deep_map_f(
            ['node', 'timelineItems', 'nodes'],
            deep_transform(['createdAt'], s2t),
        ),
        deep_map_f(
            ['node', 'timelineItems', 'nodes'],
            deep_transform(['removedAt'], s2t),
        ),
    )
    js = requests.post(
        'https://api.github.com/graphql',
        json={
            'query': query,
            'variables': {
                'owner': organization,
                'name': repo_name,
                'master':  master_branch(),
            }
        },
        headers={
            'Authorization': 'token ' + github_token,
            'Accept': 'application/vnd.github.merge-info-preview+json, application/vnd.github.antiope-preview+json',
        }
    ).json()
    return [
        transform_pr(x) for x
        in js['data']['repository']['pullRequests']['edges']
        if deep_get(['node', 'commits', 'nodes', 0, 'commit', 'pushedDate'], x)
    ]


def is_green_pull_request(pull_request):
    return pull_request.get('node', '').get('mergeStateStatus', None) == 'CLEAN'


def is_open_pull_request(pull_request):
    return pull_request.get('node', {}).get('state', '') == 'OPEN'


@curry
def sorted_(key, data, ascending):
    return sorted(data, key=key, reverse=not ascending)


@curry
def max_(key, data, default=None):
    return max(data, key=key, default=default)


def s2t(s):
    return datetime.fromisoformat(s.replace('Z', ''))


def t2s(x):
    return x.isoformat(timespec='seconds') + 'Z'


tdlt = timedelta


def is_stale_pull_request(current_time, pull_request):
    last_action = pipe(
        pull_request.get('node', {}).get('timelineItems', {}).get('nodes', []),
        filter(
            lambda x:
                x.get('label', {}).get('name', None) == split_test_label()
        ),
        max_(
            lambda x: (
                x.get('createdAt')
                if 'createdAt' in x else
                x.get('removedAt')
            ),
            default={}
        )
    )

    return 'createdAt' in last_action and (
        current_time - last_action.get('createdAt')
    ) >= split_test_stale()


@curry
def is_labeled_pull_request(pull_request, label_name):
    return any(
        deep_get(['node', 'name'], x) == label_name
        for x in deep_get(['node', 'labels', 'edges'], pull_request)
    )


def is_suitable_for_split_testing(pull_request):
    _state = deep_get_('node', 'state')
    _suites = deep_get_(
        'node', 'commits', 'nodes', 0, 'commit', 'checkSuites', 'nodes'
    )
    _runs = deep_get_('checkRuns', 'nodes')

    is_open = _state(pull_request) == 'OPEN'

    all_runs = chain_(_runs(x) for x in _suites(pull_request))

    was_built_and_tested = any(
        x.get('name') == build_test_deploy_check_name() and
        x.get('status') == 'COMPLETED' and
        x.get('conclusion') == 'SUCCESS'
        for x in all_runs
    )

    return is_open and was_built_and_tested


@curry
def allocate_traffic_to_pull_requests(
    max_parallel_split_tests,
    pull_requests,
):
    _yes, no = partition(is_suitable_for_split_testing, pull_requests)

    last_commit_time = deep_get_(
        'node', 'commits', 'nodes', 0, 'commit', 'pushedDate'
    )
    sort_pr = sorted_(last_commit_time, ascending=True)
    yes = sort_pr(_yes)

    return (
        yes[:max_parallel_split_tests],
        sort_pr(no + yes[max_parallel_split_tests:])
    )


def apply_traffic_allocation_io(pull_requests):
    pass


@curry
def partition(pred, iterable):
    yes, no = [], []
    for d in iterable:
        (yes if pred(d) else no).append(d)
    return yes, no


@curry
def first(default, iterable):
    """Returns first element of iterable
    You should also specify default value

    >>> first('none', (1, 2, 3))
    1

    >>> first('none', ())
    'none'
    """
    return more_itertools.first(iterable, default)


def extract_repo_name_from_origin(origin):
    return pipe(
        [r':([^/]*?)/([^/]*?)\.git$', r'/([^/]*?)/([^/]*?)$'],
        map(lambda x: re.search(x, origin)),
        filterempty,
        map(lambda x: (x.group(1), x.group(2))),
        first(None),
    )


def delete_dir_io(path):
    if os.path.isdir(path):
        shutil.rmtree(path)


def copy_dir_io(source, dest):
    run_io(f'yes | cp -rf {source}/. {dest}')


def allocate_traffic(pull_requests, visitors_per_day):
    pass


def secret_io(key):
    return os.environ[key]


@contextmanager
def github_io(*args, message='', allow_empty=False, **kwds):
    with tmp() as repo_path:
        github_clone_io(*args, path=repo_path, **kwds)
        yield repo_path
        github_push_io(repo_path, message, allow_empty)


def domain_io(path):
    with open('CNAME', 'r') as f:
        return f.read().strip('\r\n').strip()


def upload_to_s3_io(file_path, bucket, key):
    session = boto3.Session(
        aws_access_key_id=secret_io('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=secret_io('AWS_SECRET_ACCESS_KEY'),
    )
    s3 = session.resource('s3')
    return s3.Object(bucket, key).put(
        Body=open(file_path, 'rb'),
        ContentType='text/html',
        ACL='public-read'
        )

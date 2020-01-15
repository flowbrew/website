import os
import slack
import shlex
from subprocess import check_output, CalledProcessError

from toolz import compose, curry, pipe
from toolz.curried import map
from toolz.itertoolz import get
from functools import partial

apply = curry(lambda f, x: f(x))


def flip(f): return lambda *a: f(*reversed(a))


apply_ = flip(apply)
comp = compose
comp_ = flip(compose)
flip = comp(curry, flip)


def nt(x): return not (x)


filter = curry(filter)
get = curry(get)


def bottom(x):
    pass


force = compose(any, map(bottom))


def my_fun(x):
    return x + 1


def run(command_line):
    print('>', command_line)
    result = check_output(shlex.split(command_line)).decode("utf-8")
    print(result)
    return result


def notification(channel, text, token):
    client = slack.WebClient(token)
    response = client.chat_postMessage(
        channel=channel,
        text=text
    )
    return response["ok"]


def inject_branch_to_deployment(
    branch_name: str,
    branch_state: dict,
    deployment_state: dict,
) -> dict:
    startswith_ = flip(str.startswith)
    is_any_branch = comp(startswith_, branch_prefix)()
    is_specific_branch = comp(startswith_, b2p)
    is_master_branch = is_specific_branch(master_branch())
    is_target_branch = is_specific_branch(branch_name)

    branch_state_ = {
        add_prefix(branch_name, k): v
        for k, v in branch_state.items()
    }

    cleaned_deployment_state = {
        k: v
        for k, v in deployment_state.items()
        if is_any_branch(k) and not is_target_branch(k)
    }

    injected_state = {
        **cleaned_deployment_state,
        **branch_state_
    }

    master_state = {
        remove_prefix(k): v
        for k, v in injected_state.items()
        if is_master_branch(k)
    }

    return {
        **injected_state,
        **master_state
    }


def filesystem_to_dict(path):
    pass


def dict_to_filesystem(path, data):
    pass


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

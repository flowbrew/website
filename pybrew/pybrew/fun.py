import os
import slack
import shlex
from subprocess import check_output, CalledProcessError

from toolz import compose, curry, pipe
from toolz.curried import map

flip = lambda f: lambda *a: f(*reversed(a))
comp = compose
comp_ = flip(compose)

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

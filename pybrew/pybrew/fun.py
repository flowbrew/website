import os
import slack
import shlex
from subprocess import check_output, CalledProcessError


def my_fun(x):
    return x + 1


def run(command_line):
    print('>', command_line)
    result = str(check_output(shlex.split(command_line)))
    print(result)
    return result


def notification(channel, text, token):
    client = slack.WebClient(token)
    response = client.chat_postMessage(
        channel=channel,
        text=text
    )
    return response["ok"]

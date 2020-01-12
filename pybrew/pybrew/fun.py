import os
import slack


def my_fun(x):
    return x + 1


def notification(channel, text, token):
    client = slack.WebClient(token)
    response = client.chat_postMessage(
        channel=channel,
        text=text
    )
    return response["ok"]

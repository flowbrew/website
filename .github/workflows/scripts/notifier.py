#!/usr/bin/env python3

import os
from pybrew import notification


def make_message(environ):
    where_str = f"{environ.get('WORKFLOW', 'Unknown workflow')} of {environ.get('REPOSITORY', 'unknown repository')}/{environ.get('BRANCH_NAME', 'unknown branch')}"

    what_str = f"returned {'FAILURE ❌' if environ.get('FAILURE', True) else 'SUCCESS ✅'} on event {environ.get('EVENT_NAME', 'unknown event')}"

    last_commit_str = (
        f'Last commit was "{environ.get("HEAD_COMMIT_MESSAGE", "")}" {environ.get("HEAD_COMMIT_URL", "")}'
        if 'HEAD_COMMIT_MESSAGE' in environ else
        ''
    )

    return f'{where_str} {what_str}. {last_commit_str}'


def main(environ):
    environ['FAILURE'] = bool(environ.get('FAILURE', True))
    notification(
        channel='#website',
        text=make_message(environ),
        token=environ.get('SECRET_SLACK_BOT_TOKEN', '')
    )


if __name__ == "__main__":
    main(os.environ)

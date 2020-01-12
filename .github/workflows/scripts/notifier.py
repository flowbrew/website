#!/usr/bin/env python3

import os
from pybrew import notification


def make_message(
    FAILURE,
    WORKFLOW,
    REPOSITORY,
    BRANCH_NAME,
    EVENT_NAME,
    HEAD_COMMIT_MESSAGE,
    HEAD_COMMIT_URL
):
    where_str = f"{WORKFLOW} of {REPOSITORY}/{BRANCH_NAME}"

    what_str = f"returned {'FAILURE ❌' if FAILURE else 'SUCCESS ✅'} on event {EVENT_NAME}"

    last_commit_str = (
        f'Last commit was "{HEAD_COMMIT_MESSAGE}" {HEAD_COMMIT_URL}'
        if HEAD_COMMIT_MESSAGE else
        ''
    )

    return f'{where_str} {what_str}. {last_commit_str}'


def main(environ):
    notification(
        channel='#website',
        text=make_message(
            FAILURE=environ.get('FAILURE', 'true').lower().strip() == 'true',
            WORKFLOW=environ.get('WORKFLOW', 'Unknown workflow'),
            REPOSITORY=environ.get('REPOSITORY', 'unknown repository'),
            BRANCH_NAME=environ.get('BRANCH_NAME', 'unknown branch'),
            EVENT_NAME=environ.get('EVENT_NAME', 'unknown event'),
            HEAD_COMMIT_MESSAGE=environ.get('HEAD_COMMIT_MESSAGE', ''),
            HEAD_COMMIT_URL=environ.get('HEAD_COMMIT_URL', '')
        ),
        token=environ.get('SECRET_SLACK_BOT_TOKEN', '')
    )


if __name__ == "__main__":
    main(os.environ)

#!/usr/bin/env python3

import os
from pybrew import notification


def make_message(
    JOB_STATUS,
    WORKFLOW,
    REPOSITORY,
    BRANCH_NAME,
    EVENT_NAME,
    HEAD_COMMIT_MESSAGE,
    HEAD_COMMIT_URL
):
    where_str = f"{WORKFLOW} of {REPOSITORY}, branch '{BRANCH_NAME}'"

    what_str = f"{'SUCCESS ✅' if JOB_STATUS == 'success' else 'FAILURE ❌'} on event '{EVENT_NAME}'"

    last_commit_str = (
        f"Last commit was '{HEAD_COMMIT_MESSAGE}'\n{HEAD_COMMIT_URL}"
        if HEAD_COMMIT_MESSAGE else
        ''
    )

    return f'{what_str} on {where_str}\n{last_commit_str}\n---'


def main(environ):
    notification(
        channel='#website',
        text=make_message(
            JOB_STATUS=environ.get('JOB_STATUS', 'failure').lower(),
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
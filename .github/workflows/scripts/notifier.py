import os
from pybrew import notification


def make_message(environ):
    where_str = f'{environ.WORKFLOW} of {environ.REPOSITORY}/{environ.BRANCH_NAME}'

    what_str = f'returned {"FAILURE ❌" if environ.FAILURE else "SUCCESS ✅"} on event {environ.EVENT_NAME}'

    last_commit_str = (
        f'Last commit was "{environ.HEAD_COMMIT_MESSAGE}" {environ.HEAD_COMMIT_URL}'
        if 'HEAD_COMMIT_MESSAGE' in environ else
        ''
    )

    return f'{where_str} {what_str}. {last_commit_str}'


def main(environ):
    environ.FAILURE = bool(environ.FAILURE)
    notification(
        channel='#website',
        text=make_message(environ),
        token=environ.SECRET_SLACK_BOT_TOKEN
    )


if __name__ == "__main__":
    main(os.environ)

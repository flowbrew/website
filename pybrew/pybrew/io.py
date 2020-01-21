from .fun import *
from .images import *


def load_yaml_io(path):
    with open(path, 'r') as file:
        return yaml.safe_load(file)


def save_yaml_io(path, data):
    with open(path, 'w') as file:
        yaml.safe_dump(data, file)


def build_jekyll_io(repo_path, dest, sha, branch, **kwargs):
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
    target_repo_name: str,
    branch: str,
    event_name: str,
    head_commit_message: str,
    head_commit_url: str,
    success: bool,
    **kwargs
):
    where_str = f"{workflow} of {target_repo_name}, branch '{branch}'"

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
    **kwargs
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


def cleanup_io(**kwargs):
    notify_io_ = partial(github_action_notification_io, **kwargs)

    try:
        remove_from_github_io(**kwargs)
        notify_io_(success=True)

    except:
        notify_io_(success=False)
        raise


def cicd_io(**kwargs):
    notify_io_ = partial(github_action_notification_io, **kwargs)

    try:
        test_pybrew_io(**kwargs)
        bake_images_io(**kwargs)

        with tmp() as ws:
            build_jekyll_io(dest=ws, **kwargs)
            deploy_to_github_io(path=ws, **kwargs)
            wait_until_deployed_by_sha_io__(**kwargs)

        notify_io_(success=True)

    except:
        notify_io_(success=False)
        raise

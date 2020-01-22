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
    runslow=True,
    **kwargs
):
    run_io(f'''
        pytest -vv --color=yes --pyargs pybrew \
            {'--runslow' if runslow else ''} \
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


def bake_images_io_(
    github_username,
    github_token,
    organization,
    branch,
    repo_name,
    **kwargs
):
    def _modify_io(repo_path, new_repo_path):
        dict_to_filesystem_io(
            new_repo_path,
            filesystem_to_dict_io(repo_path)
        )
        with Path(new_repo_path):
            bake_images_io(**kwargs)
            run_io('ls -a ' + repo_path)
            run_io('ls -a ' + os.path.join(repo_path, '/assets/img_gen'))
            print('---<')
            run_io('ls -a ' + new_repo_path)
            run_io('ls -a ' + os.path.join(new_repo_path, '/assets/img_gen'))

    return github_modify_io(
        github_username=github_username,
        github_token=github_token,
        organization=organization,
        repo_name=repo_name,
        branch=branch,
        message=f'Baking images for branch {branch}',
        allow_empty=False,
        f=_modify_io
    )


def cicd_io(**kwargs):
    notify_io_ = partial(github_action_notification_io, **kwargs)

    try:
        test_pybrew_io(runslow=True, **kwargs)

        if bake_images_io_(**kwargs):
            print('Some images were baked, cancelling CI/CD')
            return

        with tmp() as ws:
            build_jekyll_io(dest=ws, **kwargs)
            deploy_to_github_io(path=ws, **kwargs)
            wait_until_deployed_by_sha_io_(domain=domain_io(ws), **kwargs)

        notify_io_(success=True)

    except:
        notify_io_(success=False)
        raise

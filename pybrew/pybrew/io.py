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
            'temp_config.yml',
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

        run_io('bundle update')
        run_io(f'jekyll build --trace -d {dest} --config temp_config.yml')


def domain_io(path):
    with open('CNAME', 'r') as f:
        return f.read().strip('\r\n').strip()


def github_action_notification_io(
    slack_token: str,
    workflow: str,
    branch: str,
    organization: str,
    repo_name: str,
    event_name: str,
    head_commit_message: str,
    head_commit_url: str,
    success: bool,
    **kwargs
):
    if workflow == 'LOCAL':
        return

    where_str = f"{workflow} of {organization}/{repo_name}, branch '{branch}'"

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
    test_deployment_repo,
    organization,
    local_run,
    **kwargs
):
    run_io(f'''
        pytest -vv --color=yes --pyargs pybrew \
            {'--runslow' if not local_run else ''} \
            --SECRET_GITHUB_WEBSITE_USERNAME={github_username} \
            --SECRET_GITHUB_WEBSITE_TOKEN={github_token} \
            --SECRET_SLACK_BOT_TOKEN={slack_token} \
            --SHA={sha} \
            --BRANCH={branch} \
            --TEST_REPOSITORY={test_deployment_repo} \
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


# def copy_io(source, dest):
#     run_io(f'cp -af {source} {dest}')


def bake_images_io_(branch, repo_path, local_run, **kwargs):
    with Path(repo_path):
        bake_images_io(**kwargs)

    if local_run:
        return

    return github_push_io(
        path=repo_path,
        message=f'Baking images for branch {branch}',
        allow_empty=False
    )


class CICDCancelled(Exception):
    pass


def _check_output(x): return check_output(x).decode('utf-8').strip('\n')


def git_branch_io(path='.'):
    with Path(path):
        return _check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'])


def git_sha_io(path='.'):
    with Path(path):
        return _check_output(['git', 'rev-parse', '--verify', 'HEAD'])


def git_origin_io(path='.'):
    with Path(path):
        return _check_output(['git', 'config', '--get', 'remote.origin.url'])


def git_repo_name_io(path):
    return re.search(r':(.*)/(.*)\.git', git_origin_io(path)).group(2)


def git_organization_io(path):
    return re.search(r':(.*)/(.*)\.git', git_origin_io(path)).group(1)


def git_head_commit_message_io(path='.'):
    with Path(path):
        return _check_output(['git', 'log', '-1', '--pretty=%B'])


def github_commit_url_io(org, name, sha):
    return f'https://github.com/{org}/{name}/commit/{sha}'


def deploy_jekyll_io(path, local_run, **kwargs):
    if local_run:
        pass
        
    else:
        deploy_to_github_io(path=path, **kwargs)
        wait_until_deployed_by_sha_io_(domain=domain_io(path), **kwargs)


def cicd_io(repo_path, **kwargs_):
    name = git_repo_name_io(repo_path)
    org = git_organization_io(repo_path)
    sha = git_sha_io(repo_path)

    kwargs = {
        **kwargs_,
        **{
            'repo_path': repo_path,
            'repo_name': name,
            'organization': org,
            'sha': sha,
            'branch': git_branch_io(repo_path),
            'head_commit_message': git_head_commit_message_io(repo_path),
            'head_commit_url': github_commit_url_io(org, name, sha),
        }
    }

    notify_io_ = partial(github_action_notification_io, **kwargs)

    try:
        test_pybrew_io(**kwargs)

        if bake_images_io_(**kwargs):
            raise CICDCancelled('Some images were baked, cancelling CI/CD')

        with tmp() as ws:
            build_jekyll_io(dest=ws, **kwargs)
            deploy_jekyll_io(path=ws, **kwargs)

        notify_io_(success=True)

    except CICDCancelled as e:
        print('CICDCancelled: ', str(e))

    except:
        notify_io_(success=False)
        raise

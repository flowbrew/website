from .fun import *

import operator
import math
import re
import tinify
import json
from cachier import cachier


def secret_io(key):
    return os.environ[key]


@curry
def cpost(cache_dir, url, data, headers):

    @cachier(cache_dir=cache_dir)
    def _cpost(url, jdata, jheaders):
        return requests.post(
            url,
            data=json.loads(jdata),
            headers=json.loads(jheaders)
        )

    return _cpost(url, json.dumps(data), json.dumps(headers))


@curry
def cget(cache_dir, url, params, headers):

    @cachier(cache_dir=cache_dir)
    def _cget(url, jparams, jheaders):
        return requests.get(
            url,
            params=json.loads(jparams),
            headers=json.loads(jheaders)
        )

    return _cget(url, json.dumps(params), json.dumps(headers))


def _google_pagespeed_io(
    google_pagespeed_key,
    url,
    category,
    is_mobile=False
):
    api_url = 'https://www.googleapis.com/pagespeedonline/v5/runPagespeed'
    headers = {
        'Accept': 'application/json',
    }
    params = {
        'url': url,
        'category': category,
        'strategy': 'mobile' if is_mobile else 'desktop',
        'key': google_pagespeed_key,
    }

    r = requests.get(api_url, params=params, headers=headers).json()

    depricated = ['first-meaningful-paint']

    return {
        k: v for k, v in r['lighthouseResult']['audits'].items() if
        k not in depricated and v['score'] is not None
    }


def google_test_page_speed_io(**kwarg):
    return _google_pagespeed_io(category='performance', **kwarg)


def google_test_page_seo_io(**kwarg):
    return _google_pagespeed_io(category='seo', **kwarg)


def yandex_speller_io(_text, use_cache=True):
    # «Проверка правописания: Яндекс.Спеллер» http://api.yandex.ru/speller/
    text = _text.replace('γδ', '')

    url = 'https://speller.yandex.net/services/spellservice.json/checkText'
    headers = {}
    params = {
        'text': text
    }

    _f = cget('.cache/yandex') if use_cache else requests.get
    r = _f(url, params=params, headers=headers).json()

    def _make_result(x):
        def _error(code):
            if code == 1:
                return 'Слова нет в словаре.'
            if code == 2:
                return 'Повтор слова.'
            if code == 3:
                return 'Неверное употребление прописных и строчных букв.'
            if code == 4:
                return 'Текст содержит слишком много ошибок.'
            return 'Неизвестная ошибка'

        err = _error(x['code'])

        if err == 'Слова нет в словаре.':
            valid_words = [
                'NToss', 'улуна', 'замурчите'
            ]
            if x['word'].lower() in (x.lower() for x in valid_words):
                return

        return {
            'error': err,
            'word': x['word'],
            'hints': x['s']
        }

    return comp(list, filterempty)(_make_result(x) for x in r)


def glvrd_proofread_io(text, use_cache=True):
    url = 'https://glvrd.ru/api/v0/@proofread/'
    headers = {}
    content = {
        'chunks': text
    }

    _f = cpost('.cache/glvrd') if use_cache else requests.post
    r = _f(url, data=content, headers=headers).json()

    total_length = comp(len, re.sub)(
        r'[А-Яа-яA-Za-z0-9-]+([^А-Яа-яA-Za-z0-9-]+)?',
        '.',
        text.strip('\n').strip()
    )

    def _process_fragment(text, hints, fragment):
        hint = hints[fragment['hint']]
        text_ = text[fragment['start']:fragment['end']]

        if (hint['name'] == 'Неверное использование косой черты' and
                text_.lower() == 'мг/г'):
            return
        if (hint['name'] == 'Необъективная оценка' and
                text_.lower() == 'простуда'):
            return
        if (hint['name'] == 'Необъективная оценка' and
                text_.lower() == 'простуда'):
            return
        if (hint['name'] == 'Предлог «от»'):
            return
        if (hint['name'] == 'Канцеляризм' and
                text_.lower() == 'лицо'):
            return

        return {
            'tab': hint['tab'],
            'penalty': hint['penalty'],
            'weight': hint['weight'],
            'name': hint['name'],
            'text': text_,
        }

    hints_ = comp(list, filterempty)([
        _process_fragment(text, r['hints'], x)
        for x in chain_(r['fragments'])
    ])

    def _calc_score(hints_, tab):
        penalty, weight_ = pipe(
            hints_,
            filter(lambda x: x['tab'] == tab),
            map(lambda x: (x['penalty'], x['weight'])),
            reduce(lambda x, y: (x[0] + y[0], x[1] + y[1]), (0.0, 0.0)),
            tuple
        )

        weight = weight_ / 100

        score1 = (
            math.floor(100.0 * math.pow(1.0 - weight /
                                        total_length, 3)) - penalty
        )

        return min(max(score1, 0.0), 100.0) / 10.0

    return {
        'red': _calc_score(hints_, 'red'),
        'blue': _calc_score(hints_, 'blue'),
        'hints': sorted(
            hints_,
            key=lambda x: x['weight'] + x['penalty'],
            reverse=True
        )
    }


def load_yaml_io(path):
    with open(path, 'r') as file:
        return yaml.safe_load(file)


def save_yaml_io(path, data):
    with open(path, 'w') as file:
        yaml.safe_dump(data, file)


def build_jekyll_io(repo_path, dest, sha, branch, local_run, **kwargs):
    with Path(repo_path):
        save_yaml_io(
            'temp_config.yml',
            {
                **load_yaml_io('_config.yml'),
                **{
                    'baseurl': (
                        '/' if local_run or branch == master_branch()
                        else branch_to_prefix(branch)
                    ),
                    'github-branch': branch,
                    'github-commit-sha': sha,
                    'no-index': branch != master_branch(),
                }
            }
        )

        if local_run:
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
    local_run: bool,
    **kwargs
):
    where_str = f"{workflow} of {organization}/{repo_name}, branch '{branch}'"

    what_str = f"{'SUCCESS ✅' if success else 'FAILURE ❌'} on event '{event_name}'"

    last_commit_str = (
        f"Last commit was '{head_commit_message}'\n{head_commit_url}"
        if head_commit_message else
        ''
    )

    text = f'{what_str} on {where_str}\n{last_commit_str}\n---'

    if local_run:
        print(text)
    else:
        notification_io(channel='#website', text=text, token=slack_token)


def cleanup_io(deployment_repo, ref_branch, **kwargs):
    notify_io_ = partial(
        github_action_notification_io,
        slack_token=secret_io('SLACK_BOT_TOKEN'),
        **kwargs
    )

    try:
        remove_from_github_io(
            github_username=secret_io('GITHUB_WEBSITE_USERNAME'),
            github_token=secret_io('GITHUB_WEBSITE_TOKEN'),
            target_repo_name=deployment_repo,
            target_branch_name=ref_branch,
            **kwargs
        )
        notify_io_(success=True)

    except:
        notify_io_(success=False)
        raise


@cachier(cache_dir='.cache/baked')
def tinify_bake_io(img: bytes, resolution: int) -> bytes:
    source = tinify.from_buffer(img)
    if resolution > 0:
        return source.resize(method='scale', width=resolution).to_buffer()
    else:
        return source.to_buffer()


def bake_images_io(
    tinify_key,
    repo_path,
    resolutions=[0, 256, 512, 1024, 2048],
    **kwargs
):
    tinify.key = tinify_key

    IMAGES_PATH = './img'
    GEN_IMAGES_PATH = './img_gen'

    def _baked_image_name(orig_name, resolution):
        root, extension = os.path.splitext(
            orig_name.replace(IMAGES_PATH, GEN_IMAGES_PATH, 1)
        )
        return (
            f'{root}_{resolution}{extension}'
            if resolution else
            f'{root}{extension}'
        )

    def _bake_image_io(path, resolution):
        path2 = _baked_image_name(path, resolution)
        os.makedirs(os.path.dirname(path2), exist_ok=True)
        with open(path, 'rb') as f, open(path2, 'wb') as f2:
            comp(f2.write, tinify_bake_io)(f.read(), resolution)

    with Path(os.path.join(repo_path, 'assets')):
        delete_dir_io(GEN_IMAGES_PATH)

        images = (
            x for x in files_io(IMAGES_PATH)
            if os.path.splitext(x)[1] in {'.jpg', '.png', '.jpeg'}
        )

        tasks = product(images, resolutions)

        [_bake_image_io(*x) for x in tasks]


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


def git_head_commit_message_io(path='.'):
    with Path(path):
        return _check_output(['git', 'log', '-1', '--pretty=%B'])


def github_commit_url_io(org, name, sha):
    return f'https://github.com/{org}/{name}/commit/{sha}'


def deploy_jekyll_io(path, local_run, deployment_repo, **kwargs):
    if local_run:
        dict_to_filesystem_io(
            './_local_deployment',
            filesystem_to_dict_io(path)
        )

    else:
        deploy_to_github_io(
            github_username=secret_io('GITHUB_WEBSITE_USERNAME'),
            github_token=secret_io('GITHUB_WEBSITE_TOKEN'),
            path=path,
            target_repo_name=deployment_repo,
            **kwargs
        )
        wait_until_deployed_by_sha_io_(domain=domain_io(path), **kwargs)


def pytest_args(mark, local_run):
    return f'''pytest 
        -vv -l -W ignore::DeprecationWarning 
        --color=yes 
        --durations=10 
        --pyargs pybrew 
        -m {mark} 
        {"--local" if local_run else ""} 
        {"--runslow" if not local_run else ""} 
        '''


def validate_pybrew_io(
    sha,
    branch,
    test_deployment_repo,
    organization,
    local_run,
    **kwargs
):
    run_io(pytest_args('pybrew', local_run) + f'''
        --SHA={sha} 
        --BRANCH={branch} 
        --TEST_REPOSITORY={test_deployment_repo} 
        --ORGANIZATION={organization}
        ''')


def build_io(**kwargs):
    bake_images_io(tinify_key=secret_io('TINIFY_KEY'), **kwargs)
    build_jekyll_io(**kwargs)


def validate_build_io(
    path,
    branch,
    local_run,
    **kwargs
):
    run_io(pytest_args('build', local_run) + f'''
        --WEBSITE_BUILD_PATH={path} 
        --BRANCH={branch}
        ''')


def deploy_io(**kwargs):
    deploy_jekyll_io(**kwargs)


def validate_deployment_io(
    repo_path,
    branch,
    local_run,
    **kwargs
):
    url = (
        f'http://127.0.0.1:4000/'
        if local_run else
        f'https://{domain_io(repo_path)}/'
    )

    baseurl = url + (
        '' 
        if local_run or branch == master_branch() else 
        branch_to_prefix(branch)
    )

    run_io(pytest_args('deployment', local_run) + f'''
        --BRANCH={branch} 
        --URL={baseurl}
        ''')


# ---


def cicd_io(repo_path, event_name, **kwargs_):
    org, name = extract_repo_name_from_origin(git_origin_io(repo_path))
    sha = git_sha_io(repo_path)

    kwargs = {
        **kwargs_,
        **{
            'repo_path': repo_path,
            'event_name': event_name,
            'repo_name': name,
            'organization': org,
            'sha': sha,
            'branch': git_branch_io(repo_path),
            'head_commit_message': git_head_commit_message_io(repo_path),
            'head_commit_url': github_commit_url_io(org, name, sha),
        }
    }

    if event_name == 'push':
        on_branch_updated_io(**kwargs)
    elif event_name == 'delete':
        ob_branch_deleted_io(**kwargs)
    else:
        raise Exception(f'Unknown event "{event_name}""')


def ob_branch_deleted_io(**kwargs):
    cleanup_io(
        **{
            **kwargs,
            **{
                'local_run': False
            }
        }
    )


def git_push_state_if_updated_io(repo_path, branch, local_run, **kwargs):
    if local_run or not git_has_unstaged_changes_io():
        return

    github_push_io(
        path=repo_path,
        message=f'CI/CD updated state of {branch}',
        allow_empty=False
    )


def on_branch_updated_io(**kwargs):
    notify_io_ = partial(
        github_action_notification_io,
        slack_token=secret_io('SLACK_BOT_TOKEN'),
        **kwargs
    )

    with tmp() as ws:
        try:
            validate_pybrew_io(**kwargs)

            build_io(dest=ws, **kwargs)
            validate_build_io(path=ws, **kwargs)

            # ---

            git_push_state_if_updated_io(**kwargs)

            # ---

            deploy_io(path=ws, **kwargs)
            validate_deployment_io(**kwargs)

            notify_io_(success=True)

        except Exception as _:
            notify_io_(success=False)
            raise

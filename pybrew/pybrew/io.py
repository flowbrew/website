from .fun import *

import operator
import math
import re
import tinify
import time
import json
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from cachier import cachier
from contextlib import contextmanager


@contextmanager
def chrome_io(*args, **kwds):
    driver = run_chrome_io(*args, **kwds)
    try:
        yield driver
    finally:
        stop_chrome_io(driver)


@try_n_times_decorator(n=3, timeout=15)
def run_chrome_io(*args, **kwds):
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-extensions')
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_experimental_option(
        'prefs', {
            'download.default_directory': '/download',
            'download.prompt_for_download': False,
            'download.directory_upgrade': True,
            'safebrowsing.enabled': True
        }
    )

    d = DesiredCapabilities.CHROME
    d['goog:loggingPrefs'] = {'browser': 'ALL'}

    driver = webdriver.Chrome(chrome_options=options, desired_capabilities=d)
    driver.implicitly_wait(10)
    return driver


def stop_chrome_io(driver):
    driver.quit()


def secret_io(key):
    return os.environ[key]


def wait_until_deployed_by_sha_io(url: str, sha: str):
    wait_until_html_deployed_io(
        url,
        lambda soup:
        soup.find('meta', {'name': 'github-commit-sha'}).get('content') == sha
    )


def wait_until_deployed_by_sha_io_(domain, branch, sha, **kwargs):
    wait_until_deployed_by_sha_io(
        'https://' + domain + '/' + branch_to_prefix(branch),
        sha
    )


@try_n_times_decorator(n=30, timeout=15)
def wait_until_html_deployed_io(url: str, f):
    # This is a workaround of caching on get requests in Github Actions
    headers = {
        'User-Agent': 'Github Action',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0',
        'RANDOM': random_str()
    }
    html = requests.get(url + '?random=' + random_str(), headers=headers).text
    soup = BeautifulSoup(html, features="html.parser")
    assert f(soup), f'Page {url} is not valid'


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


@try_n_times_decorator(n=3, timeout=15)
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

    depricated = [
        # 'first-cpu-idle'
    ]

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


@try_n_times_decorator(5, 10)
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
        yaml.safe_dump(data, file, encoding='utf-8', allow_unicode=True)


def to_jekyll_traffic_allocation(traffic_allocation):
    if not traffic_allocation:
        return dict()
    yes, _ = traffic_allocation
    v = 1 / (len(yes) + 1)
    _branch = deep_get_('node', 'headRefName')
    return {
        **{branch_to_prefix(_branch(x)).strip('/'): v for x in yes},
        **{'': v}
    }


def build_jekyll_io(
    repo_path,
    dest,
    sha,
    branch,
    local_run,
    traffic_allocation,
    **kwargs
):
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
                    'traffic-allocation': to_jekyll_traffic_allocation(
                        traffic_allocation
                    ),
                    'branch-prefix': branch_prefix()
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


def deploy_jekyll_io(path, local_run, deployment_repo, sha, **kwargs):
    if local_run:
        run_io(f'jekyll serve \
                --detach \
                -H 0.0.0.0 -P 4000 \
                -s {path} \
                -d ./_local_deployment')

    else:
        deploy_to_github_io(
            github_username=secret_io('GITHUB_WEBSITE_USERNAME'),
            github_token=secret_io('GITHUB_WEBSITE_TOKEN'),
            path=path,
            target_repo_name=deployment_repo,
            **kwargs
        )
        wait_until_deployed_by_sha_io_(
            domain=domain_io(path),
            sha=sha,
            **kwargs
        )


def pytest_args(mark, branch, local_run):
    return f'''pytest
        -vv -l
        --color=yes
        --durations=10
        --pyargs pybrew
        -m {mark}
        {"--local" if local_run else ""}
        {"--runslow" if not local_run else ""}
        {"--master" if branch == master_branch() else ""}
        '''


def validate_pybrew_io(
    sha,
    branch,
    test_deployment_repo,
    organization,
    local_run,
    **kwargs
):
    run_io(pytest_args('pybrew', branch, local_run) + f'''
        --SHA={sha}
        --BRANCH={branch}
        --TEST_REPOSITORY={test_deployment_repo}
        --ORGANIZATION={organization}
        ''')


def build_npm_io(repo_path, local_run, **kwargs):
    with Path(repo_path):
        run_io(f'npm install')

        if local_run:
            run_io(f'npm run test_build')
        else:
            run_io(f'npm run build')

        run_io(f'ls -a {repo_path}_includes/dist')

        run_io(f'npm run test')


def build_io(local_run, **__kwargs):
    kwargs = {**__kwargs, **{'local_run': local_run}}
    if not local_run:
        bake_images_io(tinify_key=secret_io('TINIFY_KEY'), **kwargs)
    build_npm_io(**kwargs)
    build_jekyll_io(**kwargs)


def validate_build_io(
    path,
    branch,
    local_run,
    **kwargs
):
    run_io(pytest_args('build', branch, local_run) + f'''
        --WEBSITE_BUILD_PATH={path}
        --BRANCH={branch}
        ''')


def deploy_io(**kwargs):
    deploy_jekyll_io(**kwargs)


def validate_deployment_io(
    repo_path,
    branch,
    local_run,
    traffic_allocation,
    **kwargs
):
    url = (
        f'http://127.0.0.1:4000'
        if local_run else
        f'https://{domain_io(repo_path)}'
    )

    baseurl = url_join(
        url,
        '' if local_run or branch == master_branch()
        else branch_to_prefix(branch)
    )

    traffic_allocation1 = to_jekyll_traffic_allocation(traffic_allocation)
    traffic_allocation2 = json.dumps(traffic_allocation1).replace("'", "")

    run_io(pytest_args('deployment', branch, local_run) + f'''
        --BRANCH={branch}
        --URL={baseurl}
        --TRAFFIC_ALLOCATION='{traffic_allocation2}'
        ''')


# ---


def cicd_io(repo_path, event_name, **kwargs_):
    start_time = time.time()

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

    if event_name == 'push' or event_name == 'schedule':
        on_branch_updated_io(**kwargs)
    elif event_name == 'delete':
        ob_branch_deleted_io(**kwargs)
    else:
        raise Exception(f'Unknown event "{event_name}""')

    assert time.time() - start_time < 600, "cicd_io is too slow, consider to speedup"


def website_traffic_io():
    return 100


def min_sufficient_traffic_for_split_test():
    return 100


def max_parallel_split_tests_io():
    return int(website_traffic_io() / min_sufficient_traffic_for_split_test())


def manage_pull_requests_io(
    branch,
    organization,
    repo_name,
    **kwargs
):
    github_token = secret_io('GITHUB_WEBSITE_TOKEN')

    def prs():
        return pull_requests_io(github_token, organization, repo_name)

    def merge_green_pull_requests_io(pull_requests):
        [
            merge_pull_request_io(github_token, x)
            for x in pull_requests if is_green_pull_request(x)
        ]
        return prs()

    def close_stale_pull_requests_io(pull_requests):
        current_time = datetime.utcnow()
        [
            close_pull_request_io(github_token, x)
            for x in pull_requests if is_stale_pull_request(current_time, x)
        ]
        return prs()

    def re_run_split_test_check_io(pull_requests):
        [
            re_run_workflow_io(github_token, x, 'split_test')
            for x in pull_requests if is_open_pull_request(x)
        ]
        return pull_requests

    def re_run_failed_builds_io(pull_requests):
        [
            re_run_workflow_io(github_token, x, 'cicd', status='failure')
            for x in pull_requests if is_open_pull_request(x)
        ]
        return pull_requests

    return pipe(
        prs(),
        merge_green_pull_requests_io,
        close_stale_pull_requests_io,
        re_run_split_test_check_io,
        re_run_failed_builds_io,
        allocate_traffic_to_pull_requests(max_parallel_split_tests_io()),
    )


def apply_labels_io(
    traffic_allocation,
    organization,
    repo_name,
    **kwargs
):
    if not traffic_allocation:
        return
    yes, no = traffic_allocation

    github_token = secret_io('GITHUB_WEBSITE_TOKEN')

    create_split_test_label_io(
        github_token,
        repository_io(github_token, organization, repo_name)['id']
    )

    [
        add_split_test_label_io(github_token, x) for x in yes
        if not is_labeled_pull_request(x, split_test_label())
    ]
    [
        remove_split_test_label_io(github_token, x) for x in no
        if is_labeled_pull_request(x, split_test_label())
    ]


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
    if not git_has_unstaged_changes_io():
        return

    if local_run:
        run_io(
            f'rsync -a --exclude "node_modules" {repo_path} /local_website/')

    else:
        github_push_io(
            path=repo_path,
            message=f'CI/CD updated state of {branch}',
            allow_empty=False
        )


def block_if_local(local_run, **kwargs):
    if local_run:
        print('Execution ended. Press Ctrl+C to exit.')
        while True:
            time.sleep(1)


def is_master(local_run, branch, **kwargs):
    return not local_run and branch == master_branch()


def on_branch_updated_io(**kwargs):
    notify_io_ = partial(
        github_action_notification_io,
        slack_token=secret_io('SLACK_BOT_TOKEN'),
        **kwargs
    )

    master = is_master(**kwargs)

    with tmp() as ws:
        try:
            validate_pybrew_io(**kwargs)

            traffic_allocation = (
                manage_pull_requests_io(**kwargs) if master else None
            )

            build_io(
                dest=ws,
                traffic_allocation=traffic_allocation,
                **kwargs
            )
            validate_build_io(path=ws, **kwargs)

            # ---

            git_push_state_if_updated_io(**kwargs)

            # ---

            deploy_io(path=ws, **kwargs)
            validate_deployment_io(
                traffic_allocation=traffic_allocation,
                **kwargs
            )

            if master:
                apply_labels_io(
                    traffic_allocation=traffic_allocation,
                    **kwargs
                )

            notify_io_(success=True)

            block_if_local(**kwargs)

        except Exception as _:
            notify_io_(success=False)
            raise

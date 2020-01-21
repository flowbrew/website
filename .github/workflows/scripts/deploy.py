#!/usr/bin/env python3

import glob
import os
import argparse
import pathlib
import fileinput
import shlex
import subprocess
import time
import urllib.request
from subprocess import check_output, CalledProcessError
from path import Path
from bs4 import BeautifulSoup


# def run(command_line):
#     return subprocess.check_output(shlex.split(command_line))


def wait_until_deployed(domain, branch, sha):
    url = (
        f'https://{domain}/branch_{branch}/' if branch != 'master' else
        f'https://{domain}/'
    )
    print('wait_until_deployed on', url)
    for _ in range(0, 60):
        try:
            request = urllib.request.Request(
                url,
                headers={'User-Agent': 'Github Action'}
            )
            with urllib.request.urlopen(request) as f:
                html = f.read().decode('utf-8')
                soup = BeautifulSoup(html, features="html.parser")
                sha_ = soup.find(
                    'meta', {'name': 'github-commit-sha'}
                ).get('content')
                if sha == sha_:
                    return True
                else:
                    raise Exception('Wrong sha')
        except Exception as e:
            print(url, e)
        time.sleep(10)
    raise Exception(f"Can't detect deployment on {url}")


def main(args):
    git = f'https://{args.username}:{args.token}@github.com/{args.repo}.git'
    website_path = './github_website_hosting'
    website_branch_path = f'{website_path}/branch_{args.branch}'
    website_master_path = f'{website_path}/branch_master'

    run('git config --global user.email "action@flowbrew.ru"')
    run('git config --global user.name "GitHub Action"')

    # loading website
    run(f'mkdir -p {website_path}')
    run(f'git clone {git} {website_path}')
    with Path(website_path):
        run_io(f'rm -rf !(branch_*|.git)')
        run_io('rm -rf !(branch_*|.git)')
        run_io('echo $?')
        run_io('ls -a')

    # updating current branch
    run_io(f'rm -rf {website_branch_path}')
    run_io(f'mkdir -p {website_branch_path}')
    run_io(f'cp -r {args.source}/. {website_branch_path}')

    # applying master branch
    if os.path.isdir(website_master_path):
        run_io(f'cp -r {website_master_path}/. {website_path}')

    # deploying
    with Path(website_path):
        run_io(f'git add --all')
        run_io(f'''git commit \
                --allow-empty \
                -m "Add changes to branch {args.branch}"''')
        run_io(f'git push')

    wait_until_deployed('flowbrew.ru', args.branch, args.sha)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--token', help='GITHUB_TOKEN')
    parser.add_argument('-u', '--username', help='GITHUB_USERNAME')
    parser.add_argument('-r', '--repo', help='Deploy repo')
    parser.add_argument('-s', '--source', help='Source')
    parser.add_argument('-b', '--branch', help='Branch')
    parser.add_argument('-S', '--sha', help='GitHub commit sha')
    main(parser.parse_args())

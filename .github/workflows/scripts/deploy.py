#!/usr/bin/env python3

import glob
import os
import argparse
import pathlib
import fileinput
import shlex
import subprocess
from subprocess import check_output, CalledProcessError
from path import Path


def run(command_line):
    return subprocess.check_output(shlex.split(command_line))


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
        run(f'rm -rf !(branch_*)')

    # updating current branch
    run(f'rm -rf {website_branch_path}')
    run(f'mkdir -p {website_branch_path}')
    run(f'cp -r {args.source}/. {website_branch_path}')

    # applying master branch
    if os.path.isdir(website_master_path):
        run(f'cp -r {website_master_path}/. {website_path}')

    # deploying
    with Path(website_path):
        print('commiting..')
        run(f'git add --all')
        out = run(f'git commit --allow-empty -m "Add changes to branch {args.branch}"')
        print('out:', out)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--token', help='GITHUB_TOKEN')
    parser.add_argument('-u', '--username', help='GITHUB_USERNAME')
    parser.add_argument('-r', '--repo', help='Deploy repo')
    parser.add_argument('-s', '--source', help='Source')
    parser.add_argument('-b', '--branch', help='Branch')
    main(parser.parse_args())

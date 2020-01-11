#!/usr/bin/env python3

import glob
import os
import argparse
import pathlib
import fileinput
import shlex
import subprocess
import yaml


def run(command_line):
    return subprocess.run(shlex.split(command_line), check=True)

def load_yaml(path):
    with open(path, 'r') as file:
        return yaml.safe_load(file)

def save_yaml(path, data):
    with open(path, 'w') as file:
        yaml.safe_dump(data, file)

def main(args):
    run(f'mkdir -p {args.dest}')

    config = load_yaml('_config.yml')
    config['baseurl'] = (
        '/' if args.branch == 'master' else '/branch_' + args.branch
        )
    config['github-repo'] = args.repo
    config['github-branch'] = args.branch
    config['github-commit-sha'] = args.sha
    config['no-index'] = args.branch != 'master'
    save_yaml('_config.yml', config)

    run(f'jekyll build --trace -d {args.dest}')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--dest', help='Where to build website')
    parser.add_argument('-r', '--repo', help='GitHub repo')
    parser.add_argument('-S', '--sha', help='GitHub commit sha')
    parser.add_argument('-b', '--branch', help='GitHub branch')
    main(parser.parse_args())

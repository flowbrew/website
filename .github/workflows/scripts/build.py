#!/usr/bin/env python3

import glob
import os
import argparse
import pathlib
import fileinput
import shlex
import subprocess


def run(command_line):
    return subprocess.run(shlex.split(command_line), check=True)


def main(args):
    run(f'mkdir -p {args.dest}')

    for line in fileinput.input(['_config.yml'], inplace=True):
        if args.branch != 'master' and 'baseurl: /' in line:
            print('baseurl: /branch_' + args.branch, end='')
        else:
            print(line, end='')

    run(f'jekyll build --trace -d {args.dest}')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--dest', help='Where to build website')
    parser.add_argument('-b', '--branch', help='Set base url')
    main(parser.parse_args())

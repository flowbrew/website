import pytest
import tempfile
import os
import yaml
from path import Path
from pybrew import build_jekyll_io, dict_to_filesystem_io, run_io, tmp, files, force, map, pipe, filter, curry
from bs4 import BeautifulSoup


# def test_build_jekyll_io(BRANCH, SHA):
#     with tmp() as source, tmp() as dest:
#         run_io(f'jekyll new --blank --force {source}')

#         build_jekyll_io(
#             source=source,
#             dest=dest,
#             sha=SHA,
#             branch=BRANCH,
#         )

#         def validate_html_io(sha, path):
#             with open(path, 'r') as f:
#                 html = f.read()
#                 soup = BeautifulSoup(html, features="html.parser")
#                 assert soup.find(
#                     'meta', {'name': 'github-commit-sha'}).get('content'
#                     ) == sha

#         [validate_html_io(SHA, x) 
#             for x in files(dest) if x.endswith('.html')]

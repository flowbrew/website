import io
import os
import re

from setuptools import find_packages
from setuptools import setup


def read(filename):
    filename = os.path.join(os.path.dirname(__file__), filename)
    text_type = type(u"")
    with io.open(filename, mode="r", encoding='utf-8') as fd:
        return re.sub(text_type(r':[a-z]+:`~?(.*?)`'), text_type(r'``\1``'), fd.read())


setup(
    name="pybrew",
    version="0.1.0",
    url="https://github.com/flowbrew/website",
    license='MIT',
    author="Aleksey Kozin",
    author_email="cirnotoss@gmail.com",
    description="Flow Brew python tools",
    packages=find_packages(exclude=('tests',)),
    install_requires=[
        'pytest',
        'pyyaml',
        'beautifulsoup4',
        'path',
        'slackclient',
        'requests',
        'toolz',
        'fn',
        'tinify',
        'more-itertools',
        'cachier',
        'selenium'
    ],
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
    ],
)

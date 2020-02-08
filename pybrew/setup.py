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
        'pytest==3.8.0',
        'pyyaml==5.1',
        'beautifulsoup4==4.6.3',
        'path==13.1.0',
        'slackclient==2.5.0',
        'requests==2.21.0',
        'toolz==0.9.0',
        'fn==0.4.3',
        'tinify==1.5.1',
        'more-itertools==4.3.0',
        'cachier==1.2.8',
        'selenium==3.141.0',
        'oauth2client==4.1.3',
        'google-api-python-client==1.7.11',
        
        # Analytics 
        'numpy',
        'scipy',
        'matplotlib',
        'ipython',
        'jupyter',
        'pandas',
        'sympy',
        'nose',
        'jupyterlab',
    ],
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
    ],
)

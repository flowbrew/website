import pytest
import os


def pytest_addoption(parser):
    parser.addoption("--SECRET_SLACK_BOT_TOKEN",
                     action="store", default="")
    parser.addoption("--SECRET_GITHUB_WEBSITE_USERNAME",
                     action="store", default="")
    parser.addoption("--SECRET_GITHUB_WEBSITE_TOKEN",
                     action="store", default="")


@pytest.fixture
def SECRET_SLACK_BOT_TOKEN(request):
    return request.config.getoption("--SLACK_BOT_TOKEN")


@pytest.fixture
def SECRET_GITHUB_WEBSITE_USERNAME(request):
    return request.config.getoption("--SECRET_GITHUB_WEBSITE_USERNAME")


@pytest.fixture
def SECRET_GITHUB_WEBSITE_TOKEN(request):
    return request.config.getoption("--SECRET_GITHUB_WEBSITE_TOKEN")


@pytest.fixture
def REPOSITORY(request):
    return os.environ.get('REPOSITORY')


# @pytest.fixture
# def WORKFLOW(request):
#     return os.environ.get('WORKFLOW')


# @pytest.fixture
# def SCRIPTS_PATH(request):
#     return os.environ.get('SCRIPTS_PATH')

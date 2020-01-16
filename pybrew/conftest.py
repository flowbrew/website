import pytest
import os


def pytest_addoption(parser):
    parser.addoption("--runslow",
                     action="store_true", default=False,
                     help="run slow tests"
                     )
    parser.addoption("--SECRET_SLACK_BOT_TOKEN",
                     action="store", default="")
    parser.addoption("--SECRET_GITHUB_WEBSITE_USERNAME",
                     action="store", default="")
    parser.addoption("--SECRET_GITHUB_WEBSITE_TOKEN",
                     action="store", default="")


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: mark test as slow to run")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--runslow"):
        return
    skip_slow = pytest.mark.skip(reason="need --runslow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)


@pytest.fixture
def SECRET_SLACK_BOT_TOKEN(request):
    return request.config.getoption("--SECRET_SLACK_BOT_TOKEN")


@pytest.fixture
def SECRET_GITHUB_WEBSITE_USERNAME(request):
    return request.config.getoption("--SECRET_GITHUB_WEBSITE_USERNAME")


@pytest.fixture
def SECRET_GITHUB_WEBSITE_TOKEN(request):
    return request.config.getoption("--SECRET_GITHUB_WEBSITE_TOKEN")


@pytest.fixture
def REPOSITORY(request):
    return os.environ.get('REPOSITORY')

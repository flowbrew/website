import pytest
import os
import json


def pytest_addoption(parser):
    parser.addoption("--runslow",
                     action="store_true", default=False,
                     help="run slow tests"
                     )
    parser.addoption("--local",
                     action="store_true", default=False,
                     help="skipping some tests unavalible in local"
                     )
    parser.addoption("--master",
                     action="store_true", default=False,
                     help="run some tests avalible only in local"
                     )
    parser.addoption("--ORGANIZATION", action="store", default="")
    parser.addoption("--URL", action="store", default="")
    parser.addoption("--TEST_REPOSITORY", action="store", default="")
    parser.addoption("--BRANCH", action="store", default="")
    parser.addoption("--SHA", action="store", default="")
    parser.addoption("--WEBSITE_BUILD_PATH", action="store", default="")
    parser.addoption("--TRAFFIC_ALLOCATION", action="store", default="")


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: mark test as slow to run")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--local"):
        skip_local = pytest.mark.skip(
            reason="can't run this test with --local"
        )
        for item in items:
            if "skip_in_local" in item.keywords:
                item.add_marker(skip_local)

    if not config.getoption("--master") and not config.getoption("--local"):
        not_in_branch = pytest.mark.skip(
            reason="can run this with --master or --local"
        )
        for item in items:
            if "not_in_branch" in item.keywords:
                item.add_marker(not_in_branch)

    if config.getoption("--runslow"):
        return
    skip_slow = pytest.mark.skip(reason="need --runslow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)


@pytest.fixture
def ORGANIZATION(request):
    return request.config.getoption("--ORGANIZATION")


@pytest.fixture
def TEST_REPOSITORY(request):
    return request.config.getoption("--TEST_REPOSITORY")


@pytest.fixture
def BRANCH(request):
    return request.config.getoption("--BRANCH")


@pytest.fixture
def SHA(request):
    return request.config.getoption("--SHA")


@pytest.fixture
def REPOSITORY(request):
    return os.environ.get('REPOSITORY')


@pytest.fixture
def WEBSITE_BUILD_PATH(request):
    return request.config.getoption("--WEBSITE_BUILD_PATH")


@pytest.fixture
def URL(request):
    return request.config.getoption("--URL")


@pytest.fixture
def TRAFFIC_ALLOCATION(request):
    return json.loads(
        request.config.getoption("--TRAFFIC_ALLOCATION")
    )

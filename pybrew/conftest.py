import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--SLACK_BOT_TOKEN", action="store", default="", help="Slack token"
    )


@pytest.fixture
def SLACK_BOT_TOKEN(request):
    return request.config.getoption("--SLACK_BOT_TOKEN")

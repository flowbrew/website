import pytest
from pybrew import my_fun, notification, run


def test_my_fun():
    assert my_fun(4) == 5


def test_notification(SLACK_BOT_TOKEN):
    assert notification(
        channel='#test',
        text='Hello World',
        token=SLACK_BOT_TOKEN
    )


def test_run():
    assert run('echo hello').starts_with('hello')
    with pytest.raises(Exception):
        run('echo23423 hello')


# def test_parallel_branching_deployment(tmp_path):
#     mk branches

#     def generate_site_content(path):
#         run()
    
#     branches = ['a', 'b', 'master']

#     a_branch = 'a'
#     b_branch = 'b'
#     master_branch = 'master'

#     deploy('./a')
#     deploy('./master')
#     deploy('./b')

#     assert reqest_html('https://') != reqest_html('https://')
#     assert reqest_html('https://') == reqest_html('https://')

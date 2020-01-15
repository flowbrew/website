import pytest
import tempfile
import os
import glob
from path import Path
from pybrew import my_fun, notification, run, pipe, map, comp, force, b2p, inject_branch_to_deployment


def test_inject_branch_to_deployment__injecting_regular():
    branch_name = 'test'

    branch_state = {
        b2p("master") + 'index.html': 'test test',
        'index.html': 'test index new',
        'some/data': 'data new',
    }

    deployment_state = {
        b2p("master") + b2p("test") + 'index.html': 'overwritten index',
        b2p("master") + 'index.html': 'master index',
        b2p("test") + 'index.html': 'overwritten index',
        b2p("test") + 'delete.html': '2 delete',
        'index.html': 'master index',
    }

    result_state = {
        b2p("master") + b2p("test") + 'index.html': 'overwritten index',
        b2p("master") + 'index.html': 'master index',
        b2p("test") + b2p("master") + 'index.html': 'test test',
        b2p("test") + 'index.html': 'overwritten index',
        b2p("test") + 'some/data': 'data new',
        'index.html': 'master index',
    }

    assert inject_branch_to_deployment(
        branch_name, branch_state, deployment_state
    ) == result_state


def test_inject_branch_to_deployment__injecting_master():
    branch_name = 'master'

    branch_state = {
        b2p("test") + 'index.html': 'overwritten index',
        'index.html': 'master index new',
        'some/data': 'some new master data',
    }

    deployment_state = {
        b2p("master") + 'index.html': 'master index',
        b2p("master") + 'some/old/data': 'old data',
        b2p("master") + 'something': '123',
        b2p("test") + 'index.html': 'test index old',
        b2p("test") + 'some/data': 'data old',
        'index.html': 'master index',
        'some/old/data': 'old data',
        'something': '123',
    }

    result_state = {
        b2p("master") + b2p("test") + 'index.html': 'overwritten index',
        b2p("master") + 'index.html': 'master index new',
        b2p("master") + 'some/data': 'some new master data',
        b2p("test") + 'index.html': 'overwritten index',
        b2p("test") + 'some/data': 'data old',
        'index.html': 'master index new',
        'some/data': 'some new master data',
    }

    assert inject_branch_to_deployment(
        branch_name, branch_state, deployment_state
    ) == result_state

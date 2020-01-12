import pytest
from pybrew import *

def test_my_fun():
    assert my_fun(4) == 5

def test_notification():
    assert notification(channel='#test', text='Hello World')

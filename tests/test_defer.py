import pytest

from defer import defer
from defer.sugar import install


@pytest.fixture(autouse=True)
def setup():
    install()
    yield


def test_defer_ast():
    calls = list()

    def foo(calls: list):
        calls.append("1") in defer
        calls.append("2")
        calls.append("3") in defer

    foo(calls)
    assert calls == ["2", "3", "1"]

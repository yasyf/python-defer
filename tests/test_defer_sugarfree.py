import pytest

from defer.sugarfree import defer as d
from defer.sugarfree import uninstall


@pytest.fixture(autouse=True)
def setup():
    uninstall()
    yield


def test_defer_static():
    calls = list()

    def foo():
        d(lambda: calls.append("bar"))
        calls.append("foo")
        d(calls.append, "baz")
        raise Exception

    try:
        foo()
    except Exception:
        pass

    assert calls == ["foo", "baz", "bar"]

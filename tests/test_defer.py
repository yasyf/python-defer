from defer import defer as d


def test_defer():
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

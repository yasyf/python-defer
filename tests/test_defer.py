def test_defer_static():
    from defer import defer as d

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


from defer import defer, install

install()


def test_defer_ast():
    calls = list()

    def foo(calls: list):
        calls.append("1") in defer
        calls.append("2")
        calls.append("3") in defer

    foo(calls)
    assert calls == ["2", "3", "1"]

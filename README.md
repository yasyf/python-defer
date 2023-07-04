# `python-defer`
### Golang-style `defer` with no decorators!

[Defer](https://go.dev/tour/flowcontrol/12) is an awesome control flow construct. Python implementations have historically relied on [cumbersome decorators](https://pypi.org/project/py-defer/) or other manual coordination. No more!

Use `python-defer` to schedule code to be run at the end of a function, whether or not anything fails. Think of it like an automagic `finally` block that you can use inline anywhere.

Check out the [blog post](https://musings.yasyf.com/bringing-gos-defer-to-python/) to learn how this was built.

## Install

```console
$ pip install python-defer
```

## Usage

The default way to use `python-defer` is true magic. Simply write your code and append an `in defer` to it.


```python
from defer import defer

def foo():
  print(", world!") in defer
  print("Hello", end="")
  # do something that might fail...
  assert 1 + 1 == 3
```

```console
$ python foo.py
Hello, World!
Traceback (most recent call last):
  File "foo.py", line 7, in <module>
    assert 1 + 1 == 3
AssertionError
```



### Sugarfree for me!

If you prefer a more explicit approach, you can use the `d` function, which takes a `lambda`.


```python
from defer.sugarfree import defer as d

def foo():
  d(print, "1")
  print("2")
  d(lambda: print("3"))
  raise RuntimeError("oh no!")
  print("4")
```

```console
$ python foo.py
2
3
1
Traceback (most recent call last):
  File "foo.py", line 7, in <module>
RuntimeError: oh no!
```

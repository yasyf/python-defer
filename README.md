# `python-defer`
### Golang-style `defer` with no decorators!

[Defer](https://go.dev/tour/flowcontrol/12) is an awesome control flow construct. Python implementations have historically relied on ugly decorators or other manual coordination. No more!

## Install

```console
$ pip install python-defer
```

## Usage

```python
from defer import defer as d

def foo():
  d(lambda: print(", world!"))
  print("Hello")
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

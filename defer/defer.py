import sys
from typing import Any, Callable, ParamSpec, TypeVar

from defer._defer import _Defer
from defer.sugar._parse import _ParseDefer

P = ParamSpec("P")
T = TypeVar("T")


class Defer:
    def __call__(self, fn: Callable[P, T], *args: P.args, **kwargs: P.kwargs):
        if sys.gettrace() is None:
            sys.settrace(_ParseDefer.IDENTITY)
        frame = sys._getframe(1)
        if not isinstance(frame.f_trace, _Defer):
            frame.f_trace = _Defer(frame.f_trace)
        frame.f_trace.push(fn, *args, **kwargs)
        frame.f_trace_lines = False

    def __contains__(self, fn: Any):
        breakpoint()
        self(fn)

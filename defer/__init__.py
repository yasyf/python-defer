import sys
from contextlib import ExitStack
from types import FrameType
from typing import Callable, Optional


class _Defer:
    def __init__(self, tracefn: Optional[Callable]) -> None:
        self.tracefn = tracefn or (lambda *_: None)

        self._stack = ExitStack()
        self._stack.__enter__()

    def push(self, fn: Callable, *args, **kwargs):
        self._stack.callback(fn, *args, **kwargs)

    def __call__(self, frame: FrameType, event: str, arg: Optional[object]):
        self.tracefn(frame, event, arg)

        match event:
            case "call":
                self._stack.__enter__()
            case "return":
                self._stack.__exit__(None, None, None)
                self._stack = ExitStack()
            case "exception":
                self._stack.__exit__(*arg)
                self._stack = ExitStack()
        return self


def defer(fn: Callable, *args, **kwargs):
    if not sys.gettrace():
        sys.settrace(lambda *_: None)

    frame = sys._getframe(1)
    if not isinstance(frame.f_trace, _Defer):
        frame.f_trace = _Defer(frame.f_trace)
    frame.f_trace.push(fn, *args, **kwargs)
    frame.f_trace_lines = False

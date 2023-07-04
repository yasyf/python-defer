from contextlib import ExitStack
from types import FrameType
from typing import Any, Callable, Optional, ParamSpec, TypeVar


P = ParamSpec("P")
T = TypeVar("T")


class _Defer:
    def __init__(self, tracefn: Optional[Callable]) -> None:
        self.tracefn = tracefn or (lambda *_: None)

        self._stack = ExitStack()
        self._stack.__enter__()

    def push(self, fn: Callable[P, T], *args: P.args, **kwargs: P.kwargs):
        self._stack.callback(fn, *args, **kwargs)

    def __call__(self, frame: FrameType, event: str, arg: Any):
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

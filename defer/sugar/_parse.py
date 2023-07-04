import sys
from ast import (
    AsyncFunctionDef,
    FunctionDef,
)
from collections import deque
from types import FrameType
from typing import Any, Callable, Optional, cast

from executing.executing import Executing, Source

from defer.errors import FreeVarsError
from defer.sugar.transformer import RewriteDefer


class _ParseDefer:
    IDENTITY = lambda *_: None  # noqa: E731

    def __init__(self, tracefn: Optional[Callable]) -> None:
        self.tracefn = tracefn or self.IDENTITY
        self.pending: deque[Executing] = deque()

    def __call__(self, frame: FrameType, event: str, arg: Any):
        self.tracefn(frame, event, arg)

        if any(
            frame.f_code.co_filename.startswith(path)
            for path in {
                sys.base_exec_prefix,
                sys.base_prefix,
                sys.exec_prefix,
                sys.prefix,
                "<frozen ",
                "<string>",
                "<pytest ",
            }
        ):
            return self

        if event != "line":
            return self

        exc = Source.executing(frame)

        if not (stmt := next(iter(exc.statements), None)):
            return self
        if isinstance(stmt, (AsyncFunctionDef, FunctionDef)):
            self.pending.append(exc)
            return self
        if not self.pending or frame.f_back is not self.pending[-1].frame.f_back:
            return self

        stmts = self.pending.pop().statements
        node = cast(FunctionDef | AsyncFunctionDef, next(iter(stmts)))
        fn = frame.f_locals[node.name]

        if fn.__module__ in sys.stdlib_module_names:
            return self
        if fn.__code__.co_freevars:
            raise FreeVarsError(fn)
        if not (ast := RewriteDefer.transform(node)):
            return self

        locals = frame.f_locals.copy()
        del locals[node.name]
        exec(compile(ast, frame.f_code.co_filename, "exec"), frame.f_globals, locals)
        frame.f_locals[node.name].__code__ = locals[node.name].__code__
        return self

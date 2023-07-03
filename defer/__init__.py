import sys
from ast import (
    AST,
    AsyncFunctionDef,
    Call,
    Compare,
    FunctionDef,
    In,
    Lambda,
    Load,
    Module,
    Name,
    NodeTransformer,
    arg,
    arguments,
    copy_location,
    fix_missing_locations,
)
from ast import (
    walk as ast_walk,
)
from contextlib import ExitStack
from types import FrameType, FunctionType
from typing import Any, Callable, Optional, ParamSpec, TypeVar, cast

from executing.executing import Executing, Source

P = ParamSpec("P")
T = TypeVar("T")


class DeferErrror(RuntimeError):
    pass


class FreeVarsError(DeferErrror):
    def __init__(self, fn: FunctionType) -> None:
        super().__init__(
            "deferred function must not have free variables",
        )
        self.add_note("free vars: " + str(list(fn.__code__.co_freevars)))


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


class RewriteDefer(NodeTransformer):
    def __init__(self, root: AST) -> None:
        super().__init__()
        self._dirty = False
        self._root = root

    @classmethod
    def transform(cls, node: FunctionDef | AsyncFunctionDef) -> Optional[Module]:
        instance = cls(node)
        node = instance.visit(node)
        if not instance._dirty:
            return None
        return fix_missing_locations(Module(body=[node], type_ignores=[]))

    def visit_Compare(self, node: Compare):
        match node:
            case Compare(ops=[In()], comparators=[Name(id="defer", ctx=Load())]):
                names = [n for n in ast_walk(node.left) if isinstance(n, Name)]
                fn = Lambda(
                    args=arguments(
                        args=[arg(arg=n.id, annotation=None) for n in names],
                        kwonlyargs=[],
                        kw_defaults=[],
                        defaults=[],
                        posonlyargs=[],
                    ),
                    body=node.left,
                )
                call = Call(
                    func=Name(id="defer", ctx=Load()), args=[fn, *names], keywords=[]
                )
                copy_location(call, node)
                self._dirty = True
                return call
            case _:
                return node

    def visit_FunctionDef(self, node: FunctionDef | AsyncFunctionDef) -> Any:
        if node is self._root:
            return self.generic_visit(node)
        return node

    visit_AsyncFunctionDef = visit_FunctionDef


class _ParseDefer:
    def __init__(self, tracefn: Optional[Callable]) -> None:
        self.tracefn = tracefn or (lambda *_: None)
        self.pending: Optional[Executing] = None

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
            assert not self.pending
            self.pending = exc
            return self
        if not self.pending or frame.f_back is not self.pending.frame.f_back:
            return self

        node = cast(FunctionDef | AsyncFunctionDef, next(iter(self.pending.statements)))
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


class Defer:
    def __call__(self, fn: Callable[P, T], *args: P.args, **kwargs: P.kwargs):
        if not sys.gettrace():
            sys.settrace(lambda *_: None)

        frame = sys._getframe(1)
        if not isinstance(frame.f_trace, _Defer):
            frame.f_trace = _Defer(frame.f_trace)
        frame.f_trace.push(fn, *args, **kwargs)
        frame.f_trace_lines = False

    def __contains__(self, fn: Any):
        return True


defer = Defer()


def install():
    print(sys.gettrace())
    sys.settrace(_ParseDefer(sys.gettrace()))

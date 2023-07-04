from types import FunctionType


class DeferErrror(RuntimeError):
    pass


class FreeVarsError(DeferErrror):
    def __init__(self, fn: FunctionType) -> None:
        super().__init__(
            "deferred function must not have free variables",
        )
        self.add_note("free vars: " + str(list(fn.__code__.co_freevars)))

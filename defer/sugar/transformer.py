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
from typing import Any, Optional


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

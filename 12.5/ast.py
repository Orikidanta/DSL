# ast.py
from abc import ABC, abstractmethod
from typing import List, Tuple, Optional

class ASTNode(ABC):
    pass

class Script:
    def __init__(self, intent: str, statements: List[ASTNode]):
        self.intent = intent
        self.statements = statements

class LabelNode(ASTNode):
    def __init__(self, name: str):
        self.name = name

class SayNode(ASTNode):
    def __init__(self, message: str):
        self.message = message

class WaitNode(ASTNode):
    def __init__(self, var_name: str):
        self.var_name = var_name

class GotoNode(ASTNode):
    def __init__(self, target: str):
        self.target = target  # ✅ 统一使用 target

class CallNode(ASTNode):
    def __init__(self, func_name: str, arg: str, result_var: Optional[str] = None):
        self.func_name = func_name
        self.arg = arg
        self.result_var = result_var

class IfNode(ASTNode):
    def __init__(
        self,
        condition: Tuple[str, str, str],
        then_body: List[ASTNode],
        elif_clauses: List[Tuple[Tuple[str, str, str], List[ASTNode]]] = None,
        else_body: List[ASTNode] = None
    ):
        self.condition = condition
        self.then_body = then_body
        self.elif_clauses = elif_clauses or []
        self.else_body = else_body if else_body is not None else []
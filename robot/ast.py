# ast.py
from abc import ABC
from typing import List, Tuple, Optional

class ASTNode(ABC):
    """所有 AST 节点的基类"""
    pass

class Script:
    """整个脚本的根节点"""
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
        self.target = target

class CallNode(ASTNode):
    def __init__(self, func_name: str, arg: str, result_var: Optional[str] = None):
        self.func_name = func_name
        self.arg = arg
        self.result_var = result_var

class IfNode(ASTNode):
    def __init__(
        self,
        condition: Tuple[str, str, str],                     # (var, op, value)
        then_body: List[ASTNode],
        elif_clauses: List[Tuple[Tuple[str, str, str], List[ASTNode]]],
        else_body: List[ASTNode]
    ):
        self.condition = condition
        self.then_body = then_body
        self.elif_clauses = elif_clauses
        self.else_body = else_body
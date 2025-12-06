# interpreter.py
from typing import Dict, List, Any, Callable, Optional
from ast import (
    Script,
    ASTNode,
    LabelNode,
    SayNode,
    WaitNode,
    GotoNode,
    CallNode,
    IfNode
)

class Interpreter:
    def __init__(self, script: Script, functions: Dict[str, Callable] = None):
        self.script = script
        self.context: Dict[str, Any] = {}
        self.functions = functions or {}
        self.label_map: Dict[str, int] = {}
        for i, stmt in enumerate(script.statements):
            if isinstance(stmt, LabelNode):
                self.label_map[stmt.name] = i

    def run(self):
        pc = 0
        statements = self.script.statements

        while pc < len(statements):
            stmt = statements[pc]

            if isinstance(stmt, SayNode):
                print(f"[Bot] {stmt.message}")

            elif isinstance(stmt, WaitNode):
                user_input = input(f"[User] Enter {stmt.var_name}: ").strip()
                self.context[stmt.var_name] = user_input

            elif isinstance(stmt, GotoNode):
                if stmt.target not in self.label_map:
                    raise RuntimeError(f"Label '{stmt.target}' not found")
                pc = self.label_map[stmt.target]
                continue

            elif isinstance(stmt, CallNode):
                if stmt.func_name not in self.functions:
                    raise RuntimeError(f"Function '{stmt.func_name}' not defined")
                func = self.functions[stmt.func_name]
                arg_value = self.context.get(stmt.arg, "")
                result = func(arg_value)
                if stmt.result_var:
                    self.context[stmt.result_var] = result

            elif isinstance(stmt, IfNode):
                cond_var, op, cond_val = stmt.condition
                actual_val = self.context.get(cond_var, "")
                match = (actual_val == cond_val) if op == "==" else (actual_val != cond_val)

                executed = False
                if match:
                    self._execute_block(stmt.then_body)
                    executed = True
                else:
                    for elif_cond, elif_body in stmt.elif_clauses:
                        var, op2, val2 = elif_cond
                        v = self.context.get(var, "")
                        ok = (v == val2) if op2 == "==" else (v != val2)
                        if ok:
                            self._execute_block(elif_body)
                            executed = True
                            break
                    if not executed and stmt.else_body:
                        self._execute_block(stmt.else_body)

            elif isinstance(stmt, LabelNode):
                pass  # 标签无操作

            else:
                raise RuntimeError(f"Unknown node type: {type(stmt)}")

            pc += 1

    def _execute_block(self, block: List[ASTNode]):
        """执行 if/elif/else 中的单条语句（简化）"""
        for stmt in block:
            if isinstance(stmt, SayNode):
                print(f"[Bot] {stmt.message}")
            elif isinstance(stmt, WaitNode):
                user_input = input(f"[User] Enter {stmt.var_name}: ").strip()
                self.context[stmt.var_name] = user_input
            elif isinstance(stmt, CallNode):
                if stmt.func_name in self.functions:
                    arg_val = self.context.get(stmt.arg, "")
                    res = self.functions[stmt.func_name](arg_val)
                    if stmt.result_var:
                        self.context[stmt.result_var] = res
            # 注意：不支持在 if 块中 goto（保持简单）
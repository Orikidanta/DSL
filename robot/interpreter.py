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
        """
        :param script: 已解析的 DSL 脚本（Script 对象）
        :param functions: 外部函数映射，如 {"check_refund": func}
        """
        self.script = script
        self.context: Dict[str, str] = {}  # 所有变量都是字符串
        self.functions = functions or {}

        # 构建标签到行号的映射
        self.label_to_pc: Dict[str, int] = {}
        for i, stmt in enumerate(script.statements):
            if isinstance(stmt, LabelNode):
                if stmt.name in self.label_to_pc:
                    raise RuntimeError(f"重复的标签: {stmt.name}")
                self.label_to_pc[stmt.name] = i

    def run(self):
        """执行整个脚本"""
        pc = 0  # program counter
        statements = self.script.statements

        while pc < len(statements):
            stmt = statements[pc]

            if isinstance(stmt, SayNode):
                # 支持简单变量插值：say "状态：{status}"
                message = self._interpolate(stmt.message)
                print(f"[Bot] {message}")

            elif isinstance(stmt, WaitNode):
                prompt = f"[User] 请输入 {stmt.var_name}："
                user_input = input(prompt).strip()
                self.context[stmt.var_name] = user_input

            elif isinstance(stmt, GotoNode):
                target = stmt.target
                if target not in self.label_to_pc:
                    raise RuntimeError(f"跳转目标不存在: label '{target}' 未定义")
                pc = self.label_to_pc[target]
                continue  # 跳过 pc += 1

            elif isinstance(stmt, CallNode):
                func_name = stmt.func_name
                arg_var = stmt.arg
                result_var = stmt.result_var

                if func_name not in self.functions:
                    raise RuntimeError(f"未定义的函数: {func_name}")

                arg_value = self.context.get(arg_var, "")
                try:
                    result = self.functions[func_name](arg_value)
                    result = str(result)  # 强制转为字符串
                    if result_var:
                        self.context[result_var] = result
                except Exception as e:
                    raise RuntimeError(f"调用函数 {func_name} 时出错: {e}")

            elif isinstance(stmt, IfNode):
                # 评估主条件
                matched = self._eval_condition(stmt.condition)
                executed = False

                if matched:
                    self._execute_block(stmt.then_body)
                    executed = True
                else:
                    # 检查 elif 分支
                    for cond, body in stmt.elif_clauses:
                        if self._eval_condition(cond):
                            self._execute_block(body)
                            executed = True
                            break
                    # 如果都没匹配，执行 else
                    if not executed and stmt.else_body:
                        self._execute_block(stmt.else_body)

            elif isinstance(stmt, LabelNode):
                # 标签本身无操作
                pass

            else:
                raise RuntimeError(f"未知的 AST 节点类型: {type(stmt).__name__}")

            pc += 1

    def _eval_condition(self, condition: tuple) -> bool:
        """评估条件 (var, op, value) -> bool"""
        var_name, op, expected_val = condition
        actual_val = self.context.get(var_name, "")
        if op == "==":
            return actual_val == expected_val
        elif op == "!=":
            return actual_val != expected_val
        else:
            raise RuntimeError(f"不支持的比较操作符: {op}")

    def _execute_block(self, block: List[ASTNode]):
        """执行 if/elif/else 块中的语句（目前只支持单条）"""
        for stmt in block:
            if isinstance(stmt, SayNode):
                msg = self._interpolate(stmt.message)
                print(f"[Bot] {msg}")
            elif isinstance(stmt, WaitNode):
                user_in = input(f"[User] 请输入 {stmt.var_name}：").strip()
                self.context[stmt.var_name] = user_in
            elif isinstance(stmt, CallNode):
                if stmt.func_name in self.functions:
                    arg_val = self.context.get(stmt.arg, "")
                    res = self.functions[stmt.func_name](arg_val)
                    if stmt.result_var:
                        self.context[stmt.result_var] = str(res)
                else:
                    raise RuntimeError(f"函数未定义: {stmt.func_name}")
            else:
                # 注意：在 if 块中暂不支持 goto（避免复杂控制流）
                # 若需支持，可递归调用主循环逻辑，但课程项目通常不要求
                raise RuntimeError(f"if 块中暂不支持语句: {type(stmt).__name__}")

    def _interpolate(self, text: str) -> str:
        """简单变量替换：将 {var} 替换为 context[var]"""
        # 只处理形如 {xxx} 的占位符
        import re
        def replacer(match):
            var_name = match.group(1)
            return self.context.get(var_name, f"{{{var_name}}}")
        return re.sub(r"\{(\w+)\}", replacer, text)
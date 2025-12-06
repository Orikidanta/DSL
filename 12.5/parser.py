# parser.py
import re
from typing import List, Tuple, Optional
from ast import Script, LabelNode, SayNode, WaitNode, GotoNode, CallNode, IfNode, ASTNode

class DSLParser:
    def __init__(self, source: str):
        lines = []
        for line in source.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                lines.append(stripped)
        self.lines = lines
        self.pos = 0

    def peek(self) -> Optional[str]:
        return self.lines[self.pos] if self.pos < len(self.lines) else None

    def consume(self) -> str:
        if self.pos >= len(self.lines):
            raise SyntaxError("Unexpected end of script")
        line = self.lines[self.pos]
        self.pos += 1
        return line

    def parse(self) -> Script:
        first_line = self.consume()
        if not first_line.startswith("intent:"):
            raise SyntaxError("Script must start with 'intent: <name>'")
        intent_name = first_line.split(":", 1)[1].strip()

        statements = []
        while self.peek() is not None:
            stmt = self.parse_statement()
            statements.append(stmt)

        return Script(intent_name, statements)

    def parse_statement(self) -> 'ASTNode':
        line = self.peek()
        if line.endswith(":") and not line.startswith(("if ", "elif ", "else:")):
            self.consume()
            label_name = line.rstrip(":")
            return LabelNode(label_name)

        elif line.startswith("say "):
            self.consume()
            match = re.match(r'say\s+"(.*)"$', line)
            if not match:
                raise SyntaxError(f"Invalid say statement: {line}")
            return SayNode(match.group(1))

        elif line.startswith("wait "):
            self.consume()
            var_name = line.split(maxsplit=1)[1]
            if not var_name.isidentifier():
                raise SyntaxError(f"Invalid variable name: {var_name}")
            return WaitNode(var_name)

        elif line.startswith("goto "):
            self.consume()
            target = line.split(maxsplit=1)[1]
            return GotoNode(target)  # ✅ 使用 target

        elif line.startswith("call "):
            self.consume()
            pattern = r'call\s+(\w+)\s*\(\s*(\w+)\s*\)(?:\s+as\s+(\w+))?'
            match = re.match(pattern, line)
            if not match:
                raise SyntaxError(f"Invalid call statement: {line}")
            func_name, arg, result_var = match.groups()
            return CallNode(func_name, arg, result_var)

        elif line.startswith("if ") or line.startswith("elif ") or line == "else:":
            return self.parse_if()

        else:
            raise SyntaxError(f"Unknown statement: {line}")

    def parse_if(self) -> IfNode:
        if_line = self.consume()
        cond_str = if_line[3:].rstrip(":").strip()
        main_cond = self.parse_condition(cond_str)
        then_body = self.parse_block()

        elif_clauses = []
        else_body = None

        while self.peek():
            next_line = self.peek()
            if next_line.startswith("elif "):
                self.consume()
                cond_str = next_line[5:].rstrip(":").strip()
                cond = self.parse_condition(cond_str)
                body = self.parse_block()
                elif_clauses.append((cond, body))
            elif next_line == "else:":
                self.consume()
                else_body = self.parse_block()
                break
            else:
                break

        return IfNode(main_cond, then_body, elif_clauses, else_body)

    def parse_condition(self, cond_str: str) -> Tuple[str, str, str]:
        cond_str = cond_str.strip()
        if "==" in cond_str:
            left, right = cond_str.split("==", 1)
            op = "=="
        elif "!=" in cond_str:
            left, right = cond_str.split("!=", 1)
            op = "!="
        else:
            raise SyntaxError(f"Only '==' and '!=' supported: {cond_str}")
        left = left.strip()
        right = right.strip().strip('"')
        if not left.isidentifier():
            raise SyntaxError(f"Left side must be identifier: {left}")
        return (left, op, right)

    def parse_block(self) -> List['ASTNode']:
        """简化版：只读一条语句（避免吃掉后续语句）"""
        if self.peek() is None:
            return []
        stmt = self.parse_statement()
        return [stmt]
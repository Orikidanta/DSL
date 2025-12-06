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
            raise SyntaxError("Unexpected end of input")
        line = self.lines[self.pos]
        self.pos += 1
        return line

    def parse(self) -> Script:
        first = self.consume()
        if not first.startswith("intent:"):
            raise SyntaxError("First line must be 'intent: <name>'")
        intent = first.split(":", 1)[1].strip()

        statements = []
        while self.peek() is not None:
            stmt = self.parse_statement()
            statements.append(stmt)

        return Script(intent, statements)

    def parse_statement(self) -> 'ASTNode':
        line = self.peek()

        # Label: e.g., "start:"
        if line.endswith(":") and not any(line.startswith(kw) for kw in ["if ", "elif ", "else:"]):
            self.consume()
            name = line.rstrip(":")
            if not name.isidentifier():
                raise SyntaxError(f"Invalid label name: {name}")
            return LabelNode(name)

        # say "message"
        elif line.startswith("say "):
            self.consume()
            match = re.match(r'say\s+"(.*)"$', line)
            if not match:
                raise SyntaxError(f"Invalid say syntax: {line} (expected: say \"...\")")
            return SayNode(match.group(1))

        # wait var_name
        elif line.startswith("wait "):
            self.consume()
            var = line.split(maxsplit=1)[1]
            if not var.isidentifier():
                raise SyntaxError(f"Invalid variable name: {var}")
            return WaitNode(var)

        # goto label
        elif line.startswith("goto "):
            self.consume()
            target = line.split(maxsplit=1)[1]
            if not target.isidentifier():
                raise SyntaxError(f"Invalid goto target: {target}")
            return GotoNode(target)

        # call func(arg) as result
        elif line.startswith("call "):
            self.consume()
            pattern = r'call\s+(\w+)\s*\(\s*(\w+)\s*\)(?:\s+as\s+(\w+))?'
            match = re.match(pattern, line)
            if not match:
                raise SyntaxError(f"Invalid call syntax: {line} (e.g., call func(x) as y)")
            func, arg, result = match.groups()
            return CallNode(func, arg, result)

        # if / elif / else
        elif line.startswith("if ") or line.startswith("elif ") or line == "else:":
            return self.parse_if()

        else:
            raise SyntaxError(f"Unknown statement: {line}")

    def parse_if(self) -> IfNode:
        main_line = self.consume()
        if not main_line.startswith("if "):
            raise SyntaxError("Expected 'if', got: " + main_line)
        cond_str = main_line[3:].rstrip(":").strip()
        main_cond = self.parse_condition(cond_str)
        then_body = self.parse_block()

        elif_clauses = []
        else_body = []

        # 处理 elif 和 else
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
                break  # 遇到非 elif/else 行，结束 if 结构

        return IfNode(main_cond, then_body, elif_clauses, else_body)

    def parse_condition(self, s: str) -> Tuple[str, str, str]:
        s = s.strip()
        if "==" in s:
            left, right = s.split("==", 1)
            op = "=="
        elif "!=" in s:
            left, right = s.split("!=", 1)
            op = "!="
        else:
            raise SyntaxError(f"Only '==' and '!=' supported in condition: {s}")
        left = left.strip()
        right = right.strip().strip('"')
        if not left.isidentifier():
            raise SyntaxError(f"Left side of condition must be identifier: {left}")
        return (left, op, right)

    def parse_block(self) -> List['ASTNode']:
        """
        简化设计：每个 if/elif/else 块只包含**一条语句**
        这是课程项目的常见简化假设，避免处理缩进或 begin/end
        """
        if self.peek() is None:
            return []
        stmt = self.parse_statement()
        return [stmt]
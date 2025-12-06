# lexer.py
import re
from enum import Enum
from dataclasses import dataclass
from typing import List

class TokenType(Enum):
    INTENT = "intent"
    MATCH = "match"
    CONTEXT = "context"
    ACTIONS = "actions"
    ASK = "ask"
    CALL_API = "call_api"
    REPLY = "reply"
    LLM_REPLY = "llm_reply"
    GOTO = "goto"
    IF = "if"
    ELSE = "else"
    IDENTIFIER = "IDENTIFIER"
    STRING = "STRING"
    REGEX = "REGEX"
    LBRACE = "{"
    RBRACE = "}"
    LBRACK = "["
    RBRACK = "]"
    LPAREN = "("
    RPAREN = ")"
    COLON = ":"
    COMMA = ","
    AND = "&&"
    OR = "||"
    NOT = "!"
    EOF = "EOF"

@dataclass
class Token:
    type: TokenType
    value: str
    line: int = 1

KEYWORDS = {t.value: t for t in [
    TokenType.INTENT, TokenType.MATCH, TokenType.CONTEXT, TokenType.ACTIONS,
    TokenType.ASK, TokenType.CALL_API, TokenType.REPLY, TokenType.LLM_REPLY,
    TokenType.GOTO, TokenType.IF, TokenType.ELSE
]}

class Lexer:
    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.line = 1

    def tokenize(self) -> List[Token]:
        tokens = []
        while self.pos < len(self.text):
            ch = self.text[self.pos]
            if ch.isspace():
                if ch == '\n':
                    self.line += 1
                self.pos += 1
                continue

            # Two-char tokens
            if self.pos + 1 < len(self.text):
                two = self.text[self.pos:self.pos+2]
                if two == '&&':
                    tokens.append(Token(TokenType.AND, '&&', self.line))
                    self.pos += 2
                    continue
                elif two == '||':
                    tokens.append(Token(TokenType.OR, '||', self.line))
                    self.pos += 2
                    continue

            if ch == '!':
                tokens.append(Token(TokenType.NOT, '!', self.line))
                self.pos += 1
            elif ch == '"':
                end = self.text.find('"', self.pos + 1)
                if end == -1:
                    raise SyntaxError(f"Unterminated string at line {self.line}")
                value = self.text[self.pos+1:end]
                tokens.append(Token(TokenType.STRING, value, self.line))
                self.pos = end + 1
            elif ch == '/':
                end = self.text.find('/', self.pos + 1)
                if end == -1:
                    raise SyntaxError(f"Unterminated regex at line {self.line}")
                value = self.text[self.pos+1:end]
                tokens.append(Token(TokenType.REGEX, value, self.line))
                self.pos = end + 1
            elif ch.isalpha() or ch == '_':
                start = self.pos
                while self.pos < len(self.text) and (self.text[self.pos].isalnum() or self.text[self.pos] == '_'):
                    self.pos += 1
                word = self.text[start:self.pos]
                tok_type = KEYWORDS.get(word, TokenType.IDENTIFIER)
                tokens.append(Token(tok_type, word, self.line))
            elif ch in '{}[]():,':
                tokens.append(Token(TokenType(ch), ch, self.line))
                self.pos += 1
            else:
                raise SyntaxError(f"Unexpected character '{ch}' at line {self.line}")
        tokens.append(Token(TokenType.EOF, "", self.line))
        return tokens
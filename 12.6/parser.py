# parser.py
from typing import List, Dict, Any, Optional
from dsl_ast import *
from lexer import Token, TokenType

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def peek(self, offset: int = 0) -> Token:
        i = self.pos + offset
        if i >= len(self.tokens):
            return self.tokens[-1]  # EOF
        return self.tokens[i]

    def consume(self, expected_type: TokenType) -> Token:
        if self.peek().type == expected_type:
            token = self.tokens[self.pos]
            self.pos += 1
            return token
        else:
            tok = self.peek()
            raise SyntaxError(
                f"Line {tok.line}: Expected {expected_type.value}, got '{tok.value}' ({tok.type.value})"
            )

    def parse_program(self) -> Program:
        intents = []
        while self.peek().type != TokenType.EOF:
            intents.append(self.parse_intent())
        return Program(intents)

    def parse_intent(self) -> Intent:
        self.consume(TokenType.INTENT)
        name = self.consume(TokenType.IDENTIFIER).value
        self.consume(TokenType.LBRACE)
        match_val = self.parse_match_clause()
        context_expr = self.parse_context_clause()
        actions = self.parse_actions_clause()
        self.consume(TokenType.RBRACE)
        return Intent(name, match_val, context_expr, actions)

    def parse_match_clause(self) -> MatchValue:
        self.consume(TokenType.MATCH)
        self.consume(TokenType.COLON)
        if (self.peek().type == TokenType.IDENTIFIER and
            self.peek().value == "llm_intent"):
            self.consume(TokenType.IDENTIFIER)  # "llm_intent"
            self.consume(TokenType.COLON)
            intent_name = self.consume(TokenType.STRING).value
            return LlmIntentMatch(intent_name)
        elif (self.peek().type == TokenType.IDENTIFIER and
              self.peek().value == "keywords"):
            self.consume(TokenType.IDENTIFIER)
            self.consume(TokenType.COLON)
            self.consume(TokenType.LBRACK)
            keywords = []
            while self.peek().type != TokenType.RBRACK:
                keywords.append(self.consume(TokenType.STRING).value)
                if self.peek().type == TokenType.COMMA:
                    self.consume(TokenType.COMMA)
            self.consume(TokenType.RBRACK)
            return KeywordsMatch(keywords)
        elif self.peek().type == TokenType.REGEX:
            pattern = self.consume(TokenType.REGEX).value
            return RegexMatch(pattern)
        else:
            tok = self.peek()
            raise SyntaxError(f"Line {tok.line}: Invalid match clause")

    def parse_context_clause(self) -> Expr:
        self.consume(TokenType.CONTEXT)
        self.consume(TokenType.COLON)
        return self.parse_expr()

    def parse_expr(self) -> Expr:
        return self.parse_or_expr()

    def parse_or_expr(self) -> Expr:
        left = self.parse_and_expr()
        while self.peek().type == TokenType.OR:
            self.consume(TokenType.OR)
            right = self.parse_and_expr()
            left = BinOpExpr(left, '||', right)
        return left

    def parse_and_expr(self) -> Expr:
        left = self.parse_term()
        while self.peek().type == TokenType.AND:
            self.consume(TokenType.AND)
            right = self.parse_term()
            left = BinOpExpr(left, '&&', right)
        return left

    def parse_term(self) -> Expr:
        if self.peek().type == TokenType.NOT:
            self.consume(TokenType.NOT)
            return NotExpr(self.parse_term())
        elif self.peek().type == TokenType.LPAREN:
            self.consume(TokenType.LPAREN)
            expr = self.parse_expr()
            self.consume(TokenType.RPAREN)
            return expr
        elif (self.peek().type == TokenType.IDENTIFIER and
              self.peek().value == "has"):
            self.consume(TokenType.IDENTIFIER)  # has
            self.consume(TokenType.LPAREN)
            field = self.consume(TokenType.IDENTIFIER).value
            self.consume(TokenType.RPAREN)
            return HasExpr(field)
        else:
            tok = self.peek()
            raise SyntaxError(f"Line {tok.line}: Unexpected token in expression: {tok.value}")

    def parse_actions_clause(self) -> List[Action]:
        self.consume(TokenType.ACTIONS)
        self.consume(TokenType.COLON)
        self.consume(TokenType.LBRACK)
        actions = []
        while self.peek().type != TokenType.RBRACK:
            actions.append(self.parse_action())
            if self.peek().type == TokenType.COMMA:
                self.consume(TokenType.COMMA)
        self.consume(TokenType.RBRACK)
        return actions

    def parse_action(self) -> Action:
        tok = self.peek()
        if tok.type == TokenType.ASK:
            return self.parse_ask_action()
        elif tok.type == TokenType.CALL_API:
            return self.parse_call_api_action()
        elif tok.type == TokenType.REPLY:
            return self.parse_reply_action()
        elif tok.type == TokenType.LLM_REPLY:
            return self.parse_llm_reply_action()
        elif tok.type == TokenType.GOTO:
            return self.parse_goto_action()
        elif tok.type == TokenType.IF:
            return self.parse_if_action()
        else:
            raise SyntaxError(f"Line {tok.line}: Unknown action: {tok.value}")

    def parse_ask_action(self) -> AskAction:
        self.consume(TokenType.ASK)
        self.consume(TokenType.LPAREN)
        field = self.consume(TokenType.STRING).value
        self.consume(TokenType.COMMA)
        prompt = self.consume(TokenType.STRING).value
        self.consume(TokenType.RPAREN)
        return AskAction(field, prompt)

    def parse_call_api_action(self) -> CallApiAction:
        self.consume(TokenType.CALL_API)
        self.consume(TokenType.LPAREN)
        service = self.consume(TokenType.STRING).value
        self.consume(TokenType.COMMA)
        args = self.parse_dict()
        self.consume(TokenType.RPAREN)
        return CallApiAction(service, args)

    def parse_dict(self) -> Dict[str, Any]:
        self.consume(TokenType.LBRACE)
        d = {}
        while self.peek().type != TokenType.RBRACE:
            key = self.consume(TokenType.STRING).value
            self.consume(TokenType.COLON)
            val = self.parse_value()
            d[key] = val
            if self.peek().type == TokenType.COMMA:
                self.consume(TokenType.COMMA)
        self.consume(TokenType.RBRACE)
        return d

    def parse_value(self) -> Any:
        if self.peek().type == TokenType.STRING:
            return self.consume(TokenType.STRING).value
        elif self.peek().type == TokenType.IDENTIFIER:
            return self.consume(TokenType.IDENTIFIER).value
        elif self.peek().type == TokenType.LBRACE:
            return self.parse_dict()
        else:
            tok = self.peek()
            raise SyntaxError(f"Line {tok.line}: Expected value, got {tok.value}")

    def parse_reply_action(self) -> ReplyAction:
        self.consume(TokenType.REPLY)
        self.consume(TokenType.LPAREN)
        tmpl = self.consume(TokenType.STRING).value
        self.consume(TokenType.RPAREN)
        return ReplyAction(tmpl)

    def parse_llm_reply_action(self) -> LlmReplyAction:
        self.consume(TokenType.LLM_REPLY)
        self.consume(TokenType.LPAREN)
        tmpl = self.consume(TokenType.STRING).value
        self.consume(TokenType.RPAREN)
        return LlmReplyAction(tmpl)

    def parse_goto_action(self) -> GotoAction:
        self.consume(TokenType.GOTO)
        self.consume(TokenType.LPAREN)
        target = self.consume(TokenType.IDENTIFIER).value
        self.consume(TokenType.RPAREN)
        return GotoAction(target)

    def parse_if_action(self) -> IfAction:
        self.consume(TokenType.IF)
        self.consume(TokenType.LPAREN)
        cond = self.parse_expr()
        self.consume(TokenType.RPAREN)
        self.consume(TokenType.LBRACE)
        then_actions = self.parse_actions_clause()
        self.consume(TokenType.RBRACE)
        else_actions = None
        if self.peek().type == TokenType.ELSE:
            self.consume(TokenType.ELSE)
            self.consume(TokenType.LBRACE)
            else_actions = self.parse_actions_clause()
            self.consume(TokenType.RBRACE)
        return IfAction(cond, then_actions, else_actions)
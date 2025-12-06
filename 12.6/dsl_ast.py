# ast.py
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Union

# --- 表达式 ---
@dataclass
class HasExpr:
    field: str

@dataclass
class NotExpr:
    expr: 'Expr'

@dataclass
class BinOpExpr:
    left: 'Expr'
    op: str   # '&&' or '||'
    right: 'Expr'

Expr = Union[HasExpr, NotExpr, BinOpExpr]

# --- 动作 ---
@dataclass
class AskAction:
    field: str
    prompt: str

@dataclass
class CallApiAction:
    service: str
    args: Dict[str, Any]

@dataclass
class ReplyAction:
    template: str

@dataclass
class LlmReplyAction:
    prompt_template: str

@dataclass
class GotoAction:
    target: str

@dataclass
class IfAction:
    condition: Expr
    then_actions: List['Action']
    else_actions: Optional[List['Action']] = None

Action = Union[AskAction, CallApiAction, ReplyAction, LlmReplyAction, GotoAction, IfAction]

# --- 匹配规则 ---
@dataclass
class LlmIntentMatch:
    intent_name: str

@dataclass
class KeywordsMatch:
    keywords: List[str]

@dataclass
class RegexMatch:
    pattern: str

MatchValue = Union[LlmIntentMatch, KeywordsMatch, RegexMatch]

# --- 意图与程序 ---
@dataclass
class Intent:
    name: str
    match: MatchValue
    context: Expr
    actions: List[Action]

@dataclass
class Program:
    intents: List[Intent]
# interpreter.py
import os
import asyncio
from typing import Dict, Any, Optional, List

import dashscope
from dashscope import Generation

from dsl_ast import *
from parser import Parser
from lexer import Lexer

# 设置 DashScope API Key
dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")
if not dashscope.api_key:
    raise EnvironmentError("请设置环境变量 DASHSCOPE_API_KEY")


class Context:
    """运行时上下文：存储槽位（如 order_id）、对话状态等"""
    def __init__(self):
        self.slots: Dict[str, Any] = {}

    def has(self, field: str) -> bool:
        return field in self.slots

    def set(self, field: str, value: Any):
        self.slots[field] = value

    def get(self, field: str, default=None):
        return self.slots.get(field, default)


class Interpreter:
    def __init__(self, program: Program):
        self.program = program

    async def detect_llm_intent(self, user_input: str) -> Optional[str]:
        """
        调用 LLM 判断用户意图，返回 llm_intent 名称（如 'query_logistics'）或 None。
        不再映射到具体 DSL 意图名。
        """
        # 收集所有可用的 llm_intent 名称
        available_intents = set()
        for intent in self.program.intents:
            if isinstance(intent.match, LlmIntentMatch):
                available_intents.add(intent.match.intent_name)

        if not available_intents:
            return None

        prompt = (
            "你是一个意图分类器，请根据用户输入选择最匹配的意图名称。\n"
            "可选意图列表：\n"
            + "\n".join(f"- {i}" for i in sorted(available_intents)) + "\n\n"
            "要求：\n"
            "1. 仅输出一个意图名称，不能有任何其他文字\n"
            "2. 必须是上述列表中的名字之一\n"
            "3. 不要加引号、括号、标点或空格\n"
            "4. 如果没有匹配，请输出 'none'\n\n"
            f"用户输入：{user_input}\n"
            f"意图："
        )

        try:
            response = Generation.call(
                model="qwen-max",
                prompt=prompt,
                temperature=0.1,
                max_tokens=10,
                timeout=10
            )
            result = response.output.text.strip()
            print(f"[DEBUG] LLM 原始输出: '{result}'")

            result_clean = result.strip('"').strip("'").strip().lower()
            if result_clean == "none":
                return None

            # 精确匹配（不区分大小写）
            for name in available_intents:
                if name.lower() == result_clean:
                    print(f"[DEBUG] LLM 意图识别为: {name}")
                    return name

            return None
        except Exception as e:
            print(f"[ERROR] LLM 调用失败: {e}")
            return None

    def evaluate_expr(self, expr: Expr, context: Context) -> bool:
        """求值布尔表达式（如 has(order_id), !has(x) 等）"""
        if isinstance(expr, HasExpr):
            return context.has(expr.field)
        elif isinstance(expr, NotExpr):
            return not self.evaluate_expr(expr.expr, context)
        elif isinstance(expr, BinOpExpr):
            left = self.evaluate_expr(expr.left, context)
            right = self.evaluate_expr(expr.right, context)
            if expr.op == '&&':
                return left and right
            elif expr.op == '||':
                return left or right
            else:
                raise ValueError(f"未知操作符: {expr.op}")
        else:
            raise TypeError(f"不支持的表达式类型: {type(expr)}")

    async def execute_action(self, action: Action, context: Context) -> Optional[str]:
        """执行单个动作，返回要回复用户的文本（如果有）"""
        if isinstance(action, AskAction):
            if context.has(action.field):
                return None
            return action.prompt

        elif isinstance(action, ReplyAction):
            reply = action.template
            for key, value in context.slots.items():
                reply = reply.replace("{{" + key + "}}", str(value))
            return reply

        elif isinstance(action, CallApiAction):
            print(f"[模拟调用API] service={action.service}, args={action.args}")
            # 模拟将参数存入上下文（实际应调用真实 API）
            for arg_name in action.args:
                context.set(arg_name, f"mock_value_{arg_name}")
            return None

        elif isinstance(action, IfAction):
            cond = self.evaluate_expr(action.condition, context)
            actions_to_run = action.then_actions if cond else (action.else_actions or [])
            for act in actions_to_run:
                reply = await self.execute_action(act, context)
                if reply is not None:
                    return reply
            return None

        elif isinstance(action, GotoAction):
            print(f"[INFO] 跳转到意图: {action.target}（未实现）")
            return None

        else:
            raise TypeError(f"未知动作类型: {type(action)}")

    async def run(self, user_input: str, context: Context) -> str:
        """
        主入口：处理用户输入，返回系统回复。
        支持同一个 LLM 意图对应多个 DSL 意图，自动选择符合条件的。
        """
        # Step 1: LLM 意图识别
        matched_llm_intent = await self.detect_llm_intent(user_input)
        if not matched_llm_intent:
            return "抱歉，我不太明白您的意思。"

        # Step 2: 找出所有匹配该 LLM 意图且 context 条件满足的 DSL 意图
        candidates = []
        for intent in self.program.intents:
            if isinstance(intent.match, LlmIntentMatch):
                if intent.match.intent_name == matched_llm_intent:
                    if self.evaluate_expr(intent.context, context):
                        candidates.append(intent)

        if not candidates:
            return "当前条件不满足，无法处理该请求。"

        # Step 3: 选择第一个符合条件的意图（未来可扩展优先级）
        selected_intent = candidates[0]
        print(f"[DEBUG] 选中意图: {selected_intent.name}")

        # Step 4: 执行动作序列
        for action in selected_intent.actions:
            reply = await self.execute_action(action, context)
            if reply is not None:
                return reply

        return "已收到您的请求。"
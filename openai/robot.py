#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DSL Chatbot Interpreter - Single file implementation
Features:
- DSL (JSON) parser for simple state-machine-based chatbot scripts
- Qwen (千问 / Dashscope) LLM adapter that reads DASHSCOPE_API_KEY from env
- Intent recognizer using the LLM adapter (expects JSON output from the model)
- Runtime actions to simulate backend operations
- Interpreter executing the DSL state machine
- Three example business scenario scripts (bank, e_commerce, it_helpdesk)
- Simple CLI interactive loop
"""

import os
import json
import argparse
import time
import re
from typing import Any, Dict, List, Optional, Tuple

# -------------- DSL Parser --------------
class DSLParseError(Exception):
    pass

class DSLParser:
    @staticmethod
    def load_from_file(path: str) -> Dict[str, Any]:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        return DSLParser.load_from_string(content)

    @staticmethod
    def load_from_string(s: str) -> Dict[str, Any]:
        try:
            cfg = json.loads(s)
        except Exception as e:
            raise DSLParseError(f"解析 JSON 失败: {e}")
        DSLParser.validate(cfg)
        return cfg

    @staticmethod
    def validate(cfg: Dict[str, Any]):
        if 'name' not in cfg or 'start_state' not in cfg or 'states' not in cfg:
            raise DSLParseError('脚本必须包含 name, start_state, states 字段')
        if cfg['start_state'] not in cfg['states']:
            raise DSLParseError('start_state 必须在 states 中定义')
        for state_name, state in cfg['states'].items():
            if 'type' not in state:
                raise DSLParseError(f'state {state_name} 缺少 type')

# -------------- Qwen (Dashscope) LLM Adapter --------------
import requests

class QwenAdapter:
    """
    Adapter for Dashscope / Qwen style API.
    Reads API key from environment variable DASHSCOPE_API_KEY.
    Recognize_intent(user_text, candidates) -> dict: {intent, confidence, slots}
    """
    def __init__(self):
        self.api_key = os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise EnvironmentError("环境变量 DASHSCOPE_API_KEY 未设置！请先设置并重启终端。")
        # Dashscope generation endpoint (as earlier used)
        self.api_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"

    def recognize_intent(self, user_text: str, candidates: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Calls Qwen to classify intent. Instructs model to return strict JSON:
        {"intent": "...", "confidence": 0.0-1.0, "slots": {...}}
        If model response can't be parsed as JSON, do a best-effort fallback.
        """
        cand_text = ""
        if candidates:
            cand_text = "候选意图：" + ", ".join(candidates) + "\n"

        # Prompt: ask for strict JSON output
        prompt = (
            "你是一个意图识别模块。"
            "根据用户输入判断其意图并以严格的 JSON 格式输出，"
            "不要多余说明。输出结构："
            '{"intent": "intent_name", "confidence": 0.0, "slots": {}}' "\n"
            + cand_text +
            f"用户：{user_text}"
        )

        payload = {
            # some Dashscope endpoints accept "model" and "input". If your API expects different fields,
            # adapt payload accordingly. We try a simple form and parse common response shapes below.
            "model": "qwen-turbo",
            "input": prompt
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        try:
            resp = requests.post(self.api_url, headers=headers, json=payload, timeout=12)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            # Network / HTTP error -> return unknown with error message
            return {"intent": "unknown", "confidence": 0.0, "slots": {}, "error": str(e)}

        # Qwen / Dashscope responses may have different shapes. Try several common paths.
        possible_texts = []

        # common possibility 1: data["output"]["text"] -> list of strings
        out = data.get("output", {})
        if isinstance(out, dict):
            t = out.get("text")
            if isinstance(t, list):
                possible_texts.extend(t)
            elif isinstance(t, str):
                possible_texts.append(t)

        # possibility 2: data["output"]["choices"][0]["message"]["content"]
        choices = data.get("output", {}).get("choices") or data.get("choices")
        if isinstance(choices, list) and len(choices) > 0:
            first = choices[0]
            # try several nested fields
            msg = None
            if isinstance(first, dict):
                # chat-style
                msg = first.get("message", {}).get("content")
                if not msg:
                    # maybe text
                    mp = first.get("text")
                    if mp:
                        msg = mp
                if msg:
                    possible_texts.append(msg)

        # possibility 3: data["response"] or other top-level text
        for k in ("response", "text", "result"):
            v = data.get(k)
            if isinstance(v, str):
                possible_texts.append(v)
            if isinstance(v, list):
                possible_texts.extend(v)

        # join candidate outputs and attempt to parse JSON from first good candidate
        for raw in possible_texts:
            if not raw:
                continue
            raw_str = raw.strip()
            # if raw starts with JSON object, try parse directly
            if raw_str.startswith("{"):
                try:
                    parsed = json.loads(raw_str)
                    # ensure keys
                    intent = parsed.get("intent", "unknown")
                    conf = float(parsed.get("confidence", 0.0))
                    slots = parsed.get("slots", {}) or {}
                    return {"intent": intent, "confidence": conf, "slots": slots}
                except Exception:
                    # try to extract JSON blob by regex
                    m = re.search(r"\{.*\}", raw_str, flags=re.DOTALL)
                    if m:
                        try:
                            parsed = json.loads(m.group(0))
                            intent = parsed.get("intent", "unknown")
                            conf = float(parsed.get("confidence", 0.0))
                            slots = parsed.get("slots", {}) or {}
                            return {"intent": intent, "confidence": conf, "slots": slots}
                        except Exception:
                            pass
            else:
                # maybe model returned one-word intent like "check_balance"
                token = raw_str.splitlines()[0].strip()
                # if token looks like a single word, return it
                if re.fullmatch(r"[A-Za-z0-9_\\-]+", token):
                    return {"intent": token.lower(), "confidence": 0.6, "slots": {}}
                # if contains ":" and looks like key:value style, try to find intent:
                kv_m = re.search(r"intent\\s*[:=]\\s*([A-Za-z0-9_\\-]+)", raw_str, flags=re.I)
                if kv_m:
                    return {"intent": kv_m.group(1).lower(), "confidence": 0.6, "slots": {}}
                # else continue trying others

        # if nothing matched, fallback to unknown with raw included
        return {"intent": "unknown", "confidence": 0.0, "slots": {}, "raw": possible_texts[:1]}

# -------------- Intent Recognizer (wrapper) --------------
class IntentRecognizer:
    def __init__(self, llm_adapter: QwenAdapter):
        self.llm = llm_adapter

    def recognize(self, user_text: str, candidates: Optional[List[str]] = None) -> Tuple[str, float, Dict[str, Any]]:
        res = self.llm.recognize_intent(user_text, candidates=candidates)
        intent = res.get("intent", "unknown")
        try:
            confidence = float(res.get("confidence", 0.0))
        except Exception:
            confidence = 0.0
        slots = res.get("slots", {}) or {}
        return intent, confidence, slots

# -------------- Runtime Actions --------------
class RuntimeActions:
    def __init__(self, ctx: Dict[str, Any]):
        self.ctx = ctx

    def get_balance(self, params: Dict[str, Any]) -> Dict[str, Any]:
        # simulate reading account and storing into context for template use
        bal = {"balance": "3,452.78"}
        # also store into ctx.vars so templates using {vars[balance]} work
        self.ctx.setdefault("vars", {})["balance"] = bal["balance"]
        return bal

    def create_transfer(self, params: Dict[str, Any]) -> Dict[str, Any]:
        amount = params.get("amount") or params.get("slots", {}).get("amount") or self.ctx.get("vars", {}).get("amount") or "0"
        tx = {"status": "ok", "tx_id": f"tx_{int(time.time())}", "amount": amount}
        return tx

    def lookup_order(self, params: Dict[str, Any]) -> Dict[str, Any]:
        order_id = params.get("order_id") or params.get("slots", {}).get("order_id") or "UNKNOWN"
        return {"order_id": order_id, "status": "in_transit", "eta": "2 days"}

    def request_refund(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "refund_requested", "case_id": f"case_{int(time.time())}"}

    def reset_password(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "reset_email_sent"}

# -------------- Interpreter / Runtime --------------
class Interpreter:
    def __init__(self, script: Dict[str, Any], llm_adapter: QwenAdapter):
        DSLParser.validate(script)
        self.script = script
        self.state = script["start_state"]
        self.context: Dict[str, Any] = {"vars": {}, "script": script.get("name")}
        self.llm_adapter = llm_adapter
        self.intent_recognizer = IntentRecognizer(self.llm_adapter)
        self.actions = RuntimeActions(self.context)
        self.action_map = {
            "get_balance": self.actions.get_balance,
            "create_transfer": self.actions.create_transfer,
            "lookup_order": self.actions.lookup_order,
            "request_refund": self.actions.request_refund,
            "reset_password": self.actions.reset_password,
        }

    def _render_text(self, text: str) -> str:
        """
        Simple templating:
        - replace {vars[KEY]} with self.context['vars'][KEY]
        - replace {last_action_result[KEY]} with self.context.get('last_action_result', {})[KEY]
        - fallback to Python format with context.vars flattened (if safe)
        """
        out = text

        # replace {vars[...]} occurrences
        def repl_vars(m):
            key = m.group(1)
            return str(self.context.get("vars", {}).get(key, ""))

        out = re.sub(r"\{vars\[(.*?)\]\}", repl_vars, out)

        # replace {last_action_result[...] }
        def repl_last(m):
            key = m.group(1)
            return str(self.context.get("last_action_result", {}).get(key, ""))

        out = re.sub(r"\{last_action_result\[(.*?)\]\}", repl_last, out)

        # also support simple {vars.KEY} style
        out = re.sub(r"\{vars\.([A-Za-z0-9_]+)\}", lambda m: str(self.context.get("vars", {}).get(m.group(1), "")), out)

        # If there are leftover {key}, try to format with vars
        try:
            out = out.format(**(self.context.get("vars", {})))
        except Exception:
            # ignore formatting errors
            pass

        return out

    def _eval_assigns(self, assign_map: Dict[str, str], slots: Dict[str, Any]):
        for k, expr in (assign_map or {}).items():
            if isinstance(expr, str) and expr.startswith("$slot."):
                sname = expr.split(".", 1)[1]
                self.context.setdefault("vars", {})[k] = slots.get(sname)
            else:
                self.context.setdefault("vars", {})[k] = expr

    def _call_action(self, action_name: str, params: Dict[str, Any]) -> Any:
        fn = self.action_map.get(action_name)
        if not fn:
            # unknown action -> return None
            return None
        return fn(params)

    def _choose_transition(self, state_obj: Dict[str, Any], intent: Optional[str], confidence: float) -> Optional[Dict[str, Any]]:
        trans_list = state_obj.get("transitions") or []
        # exact match
        for tr in trans_list:
            when = tr.get("when")
            if when and intent and when.lower() == intent.lower():
                # check confidence threshold if present
                if confidence >= tr.get("confidence_threshold", 0.0):
                    return tr
        # fallback
        for tr in trans_list:
            if tr.get("when") == "$fallback":
                return tr
        # always
        for tr in trans_list:
            if tr.get("when") == "$always":
                return tr
        return None

    def _apply_transition(self, trans: Dict[str, Any], slots: Dict[str, Any]):
        if not trans:
            return
        self._eval_assigns(trans.get("assign") or {}, slots)
        to = trans.get("to")
        if to:
            self.state = to

    def run_once(self) -> Tuple[Optional[str], bool]:
        """
        Execute until an output is produced that expects user input (prompt)
        or the script ends. Returns (output_text_or_None, finished_bool).
        """
        states = self.script["states"]
        if self.state not in states:
            return (f"ERROR: Unknown state {self.state}", True)
        cur = states[self.state]
        t = cur.get("type")

        if t == "reply":
            out = self._render_text(cur.get("text", ""))
            # run any actions defined in the state (side-effect)
            for a in cur.get("actions") or []:
                res = self._call_action(a, {})
                if isinstance(res, dict):
                    self.context["last_action_result"] = res
            # transition by $always or first matching
            trans = self._choose_transition(cur, None, 1.0)
            if trans:
                self._apply_transition(trans, {})
            return (out, False)

        elif t == "prompt":
            # display prompt and wait for user input
            out = self._render_text(cur.get("text", ""))
            return (out, False)

        elif t == "action":
            # execute actions then choose transition
            for a in cur.get("actions") or []:
                res = self._call_action(a, {})
                if isinstance(res, dict):
                    self.context["last_action_result"] = res
            trans = self._choose_transition(cur, None, 1.0)
            if trans:
                self._apply_transition(trans, {})
            return (None, False)

        elif t == "end":
            return (cur.get("text", "Bye."), True)

        else:
            return (f"ERROR: Unknown state type {t}", True)

    def handle_user_input(self, user_text: str) -> Tuple[str, bool]:
        """
        When current state is a 'prompt', call this with user's input.
        Returns (bot_output_text_or_None, finished_bool)
        """
        cur = self.script["states"][self.state]
        # candidate intents (transitions that are not special)
        cand = [tr["when"] for tr in (cur.get("transitions") or []) if isinstance(tr.get("when"), str) and not tr.get("when").startswith("$")]
        intent, conf, slots = self.intent_recognizer.recognize(user_text, candidates=cand)
        # store a bit of user text maybe into vars
        self.context.setdefault("vars", {})["last_user_text"] = user_text

        chosen = self._choose_transition(cur, intent, conf)
        if not chosen:
            # fallback
            chosen = self._choose_transition(cur, "unknown", 0.0)

        # transition-level actions (if any)
        if chosen and chosen.get("actions"):
            for a in chosen.get("actions"):
                res = self._call_action(a, {"slots": slots})
                if isinstance(res, dict):
                    self.context["last_action_result"] = res

        # apply assigns from transition (e.g., assign amount)
        if chosen:
            self._apply_transition(chosen, slots)

        # move to next state's behavior
        next_state = self.script["states"].get(self.state)
        if not next_state:
            return (f"ERROR: Undefined next state {self.state}", True)

        stype = next_state.get("type")
        if stype == "reply":
            txt = self._render_text(next_state.get("text", ""))
            # apply any immediate $always transition on reply
            t = self._choose_transition(next_state, None, 1.0)
            if t:
                self._apply_transition(t, {})
            return (txt, False)
        elif stype == "prompt":
            txt = self._render_text(next_state.get("text", ""))
            return (txt, False)
        elif stype == "action":
            for a in next_state.get("actions") or []:
                res = self._call_action(a, {})
                if isinstance(res, dict):
                    self.context["last_action_result"] = res
            t = self._choose_transition(next_state, None, 1.0)
            if t:
                self._apply_transition(t, {})
            return (None, False)
        elif stype == "end":
            return (next_state.get("text", "Bye."), True)
        else:
            return (f"ERROR: Unknown next state type {stype}", True)

# -------------- Example Scripts --------------
examples = {
    "bank": {
        "name": "BankBot",
        "start_state": "s_greet",
        "states": {
            "s_greet": {"type": "reply", "text": "您好！我是银行智能客服。", "transitions": [{"when": "$always", "to": "s_ask"}]},
            "s_ask": {
                "type": "prompt",
                "text": "我可以帮您：查询余额 / 发起转账。请告诉我您要做什么（例如：查余额 / 我想转账 100 元）",
                "transitions": [
                    {"when": "check_balance", "to": "s_show_balance"},
                    {"when": "transfer", "to": "s_confirm_transfer", "assign": {"amount": "$slot.amount"}},
                    {"when": "$fallback", "to": "s_confused"}
                ],
            },
            "s_show_balance": {"type": "action", "actions": ["get_balance"], "transitions": [{"when": "$always", "to": "s_reply_balance"}]},
            "s_reply_balance": {"type": "reply", "text": "您当前的可用余额为 {vars[balance]}。", "transitions": [{"when": "$always", "to": "s_ask"}]},
            "s_confirm_transfer": {"type": "reply", "text": "您要转账的金额是 {vars[amount]} 元。请确认是否继续（是/否）。", "transitions": [{"when": "$always", "to": "s_confirm_wait"}]},
            "s_confirm_wait": {
                "type": "prompt",
                "text": "请回答：是 或 否",
                "transitions": [
                    {"when": "confirm", "to": "s_do_transfer"},
                    {"when": "deny", "to": "s_cancel_transfer"},
                    {"when": "$fallback", "to": "s_confused"}
                ]
            },
            "s_do_transfer": {"type": "action", "actions": ["create_transfer"], "transitions": [{"when": "$always", "to": "s_transfer_done"}]},
            "s_transfer_done": {"type": "reply", "text": "转账已受理，交易号 {last_action_result[tx_id]}，金额 {last_action_result[amount]}。", "transitions": [{"when": "$always", "to": "s_end"}]},
            "s_cancel_transfer": {"type": "reply", "text": "已取消转账。需要其他帮助吗？", "transitions": [{"when": "$always", "to": "s_ask"}]},
            "s_confused": {"type": "reply", "text": "抱歉，我没听清您的意图。请尝试说：查余额 / 我想转账 100 元。", "transitions": [{"when": "$always", "to": "s_ask"}]},
            "s_end": {"type": "end", "text": "感谢使用，再见！"}
        }
    },

    "e_commerce": {
        "name": "ShopBot",
        "start_state": "intro",
        "states": {
            "intro": {"type": "reply", "text": "欢迎来到电商客服。", "transitions": [{"when": "$always", "to": "ask"}]},
            "ask": {
                "type": "prompt",
                "text": "我可以帮您查询订单或申请退货，请描述（例如：我的订单 12345 在哪儿 / 我要退货）",
                "transitions": [
                    {"when": "order_status", "to": "lookup"},
                    {"when": "return_request", "to": "refund"},
                    {"when": "$fallback", "to": "confused"}
                ]
            },
            "lookup": {"type": "action", "actions": ["lookup_order"], "transitions": [{"when": "$always", "to": "reply_lookup"}]},
            "reply_lookup": {"type": "reply", "text": "订单 {last_action_result[order_id]} 的状态：{last_action_result[status]}，预计到达：{last_action_result[eta]}。", "transitions": [{"when": "$always", "to": "ask"}]},
            "refund": {"type": "action", "actions": ["request_refund"], "transitions": [{"when": "$always", "to": "reply_refund"}]},
            "reply_refund": {"type": "reply", "text": "已为您发起退货申请，工单号 {last_action_result[case_id]}。", "transitions": [{"when": "$always", "to": "ask"}]},
            "confused": {"type": "reply", "text": "抱歉，无法识别您的请求。您可以说：查询订单 12345 或 我要退货。", "transitions": [{"when": "$always", "to": "ask"}]}
        }
    },

    "it_helpdesk": {
        "name": "ITDesk",
        "start_state": "start",
        "states": {
            "start": {"type": "reply", "text": "IT 支持小助手在线。", "transitions": [{"when": "$always", "to": "ask"}]},
            "ask": {
                "type": "prompt",
                "text": "请描述故障，例如：我忘记密码 / 网络连不上",
                "transitions": [
                    {"when": "password_reset", "to": "do_reset"},
                    {"when": "network_issue", "to": "create_ticket"},
                    {"when": "$fallback", "to": "confused"}
                ]
            },
            "do_reset": {"type": "action", "actions": ["reset_password"], "transitions": [{"when": "$always", "to": "reply_reset"}]},
            "reply_reset": {"type": "reply", "text": "已发送重置密码邮件。", "transitions": [{"when": "$always", "to": "end"}]},
            "create_ticket": {"type": "reply", "text": "已为您创建工单，技术人员会尽快联系。", "transitions": [{"when": "$always", "to": "end"}]},
            "confused": {"type": "reply", "text": "抱歉没能理解您的问题，请具体描述。", "transitions": [{"when": "$always", "to": "ask"}]},
            "end": {"type": "end", "text": "谢谢，祝您工作顺利！"}
        }
    }
}

# -------------- CLI / Interactive runner --------------
def run_interactive(script_cfg: Dict[str, Any]):
    try:
        adapter = QwenAdapter()
    except Exception as e:
        print("LLM Adapter 初始化失败：", e)
        return

    interp = Interpreter(script_cfg, adapter)
    # initial step(s)
    out, finished = interp.run_once()
    if out:
        print("Bot:", out)
    while not finished:
        cur_state = interp.state
        cur = script_cfg["states"][cur_state]
        if cur.get("type") == "prompt":
            user = input("You: ").strip()
            if user.lower() in ("exit", "quit"):
                print("退出会话。")
                break
            out, finished = interp.handle_user_input(user)
            if out:
                print("Bot:", out)
        else:
            out, finished = interp.run_once()
            if out:
                print("Bot:", out)
    print("--- 会话结束 ---")

# -------------- Main --------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--script", "-s", type=str, help="内置示例: bank | e_commerce | it_helpdesk, 或传入 JSON 脚本文件路径")
    args = parser.parse_args()
    if not args.script:
        print("请选择内置示例脚本: bank, e_commerce, it_helpdesk")
        which = input("选择: ").strip()
        if which not in examples:
            print("未知示例，退出。")
            return
        run_interactive(examples[which])
    else:
        if args.script in examples:
            run_interactive(examples[args.script])
        else:
            # assume path
            try:
                cfg = DSLParser.load_from_file(args.script)
            except Exception as e:
                print("读取脚本失败:", e)
                return
            run_interactive(cfg)

if __name__ == "__main__":
    main()

# main.py（修改部分）
import json
from qwen_client import call_qwen_with_state
from dsl_loader import load_dsl
from context import Context
from logger import setup_logger  # 👈 新增导入

EXIT_KEYWORDS = {'退出', '结束', '再见', 'bye', 'exit', 'quit'}

# 初始化日志器
logger = setup_logger()
context = Context()

def main_v2():
    with open('rules.txt', encoding='utf-8') as f:
        rules = load_dsl(f.read())

    context = Context()
    history = []
    pending_field = None

    logger.info("🤖 客服机器人 v2 启动！")

    while True:
        try:
            user_input = input("👤 用户: ").strip()
        except EOFError:
            break

        if user_input in {'q'}:
            logger.info("👋 用户主动退出")
            break

        if user_input in EXIT_KEYWORDS or user_input.lower() in EXIT_KEYWORDS:
            logger.info("🔄 用户触发会话重置")
            context.clear()
            history.clear()
            pending_field = None
            print("用户退出会话，系统已重置状态。")
            print("您好！请问是要查物流、投诉还是退款？")
            continue

        # 处理 pending 字段
        if pending_field is not None:
            context.set(pending_field, user_input)
            logger.info(f"✅ 记录字段: {pending_field} = {user_input}")
            pending_field = None

        history.append({"role": "user", "content": user_input})

        # 调用 Qwen
        state = call_qwen_with_state(user_input)  # 注意：不再传 history（简化）
        scene = state.get("scene", "other")
        status = state.get("status", "unknown")
        slots = state.get("slots", {})

        # 自动将 LLM 提取的槽位写入上下文
        for key, value in slots.items():
            context.set(key, value)
            logger.debug(f"📥 从 LLM 提取槽位: {key} = {value}")

        logger.debug(f"🧠 Qwen 输出: scene='{scene}', status='{status}', slots={slots}")
        logger.debug(f"📦 上下文: {context.data}")

        # 匹配规则
        matched = False
        for rule in rules:
            if rule.get('scene') == scene and rule.get('status') == status:
                matched = True
                logger.info(f"🎯 匹配规则: [{scene}/{status}]")
                for action in rule['actions']:
                    if action['type'] == 'ask':
                        field = action['field']
                        prompt = action.get('prompt', f"请输入 {field}：")
                        print(f"💬 系统: {prompt}")
                        history.append({"role": "assistant", "content": prompt})
                        pending_field = field
                        break
                    elif action['type'] == 'reply':
                        msg = context.render(action['message'])
                        print(f"💬 系统: {msg}")
                        history.append({"role": "assistant", "content": msg})
                break

        if not matched:
            msg = "我不太确定您的需求，请说明是要查物流、投诉还是退款？"
            print(f"💬 系统: {msg}")
            history.append({"role": "assistant", "content": msg})
            logger.warning(f"❓ 未匹配任何规则: scene='{scene}', status='{status}'")

if __name__ == "__main__":
    main_v2()
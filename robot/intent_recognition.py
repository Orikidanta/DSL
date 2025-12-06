# intent_recognition.py
import os
from dotenv import load_dotenv
from dashscope import Generation
load_dotenv()

API_KEY = os.getenv("DASHSCOPE_API_KEY")
if not API_KEY:
    raise RuntimeError("请在 .env 中设置 DASHSCOPE_API_KEY")

def recognize_intent(user_input: str, available_intents: list) -> str:
    """
    使用 Qwen 模型识别用户输入的意图
    :param user_input: 用户的自然语言输入
    :param available_intents: 系统支持的意图列表，如 ["refund", "order_status"]
    :return: 匹配的 intent 名称，或 "unknown"
    """
    intent_list_str = ", ".join(f'"{i}"' for i in available_intents)

    prompt = (
        f"你是一个客服意图分类器。请根据用户输入，从以下选项中选择最匹配的意图：\n"
        f"[{intent_list_str}]\n\n"
        f"要求：只输出意图名称，不要解释，不要加引号，不要换行。\n\n"
        f"用户输入：{user_input}\n"
        f"意图："
    )

    try:
        response = Generation.call(
            model="qwen-plus",          # 也可用 qwen-max, qwen-turbo（更快更便宜）
            api_key=API_KEY,
            prompt=prompt,
            temperature=0.0,
            max_tokens=10,
            result_format="text"
        )

        if response.status_code == 200:
            intent = response.output.text.strip().strip('"').strip()
            if intent in available_intents:
                return intent
            else:
                return "unknown"
        else:
            print(f"⚠️ Qwen API 错误: {response.code} - {response.message}")
            return "unknown"

    except Exception as e:
        print(f"⚠️ 调用 Qwen 时发生异常: {e}")
        return "unknown"
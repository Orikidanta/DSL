# qwen_client.py
import os
import json
import dashscope
from dashscope import Generation

dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")

def call_qwen_with_state(user_input: str, history: list = None) -> dict:
    """
    调用 Qwen，返回结构化状态：
    {
      "scene": "logistics",          # 主场景
      "status": "need_order_id"      # 子状态
    }
    
    支持的 scene: logistics, complaint, refund, other
    支持的 status 示例:
      - logistics: ["need_order_id", "ready_to_query"]
      - complaint: ["need_type", "recorded"]
      - refund: ["need_reason", "processing"]
    """
    # 构建对话历史（可选）
    chat_history = ""
    if history:
        for turn in history:
            chat_history += f"用户: {turn['user']}\n系统: {turn['bot']}\n"

    prompt = f"""
你是一个智能客服状态机。请根据以下对话，严格输出一个 JSON 对象，包含：
- "scene": 主场景，必须是以下之一：logistics, complaint, refund, other
- "status": 子状态，描述当前需要做什么或处于什么阶段

规则：
1. 如果用户首次提到物流 → scene=logistics, status=need_order_id
2. 如果用户已提供订单号 → status=ready_to_query
3. 如果用户首次投诉 → scene=complaint, status=need_type
4. 如果用户已说明投诉类型 → status=recorded
5. 如果用户首次申请退款 → scene=refund, status=need_reason
6. 如果用户已说明退款原因 → status=processing
7. 其他情况 → scene=other, status=unknown

对话历史：
{chat_history}
最新用户输入：{user_input}

只输出 JSON，不要任何其他文字、解释或 Markdown。
"""

    try:
        response = Generation.call(
            model="qwen-max",
            prompt=prompt,
            temperature=0.1,
            max_tokens=80,
            result_format="text"
        )
        text = response.output.text.strip()
        # 清理可能的 Markdown
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        state = json.loads(text)
        # 安全校验
        if state.get("scene") not in {"logistics", "complaint", "refund", "other"}:
            state["scene"] = "other"
        return state
    except Exception as e:
        print(f"⚠️ Qwen 状态解析失败: {e}")
        return {"scene": "other", "status": "unknown"}
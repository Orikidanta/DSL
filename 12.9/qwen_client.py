# qwen_client.py
import os
import json
import dashscope
from dashscope import Generation

dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")  

def call_qwen_with_state(user_input: str, history: list = None) -> dict:
    """
    调用 Qwen，返回结构化状态。
    注意：user_input 已包含在 history 最后一条中，此处保留仅为兼容。
    """
    if not history:
        history = [{"role": "user", "content": user_input}]

    # ✅ 构建完整的对话文本（包括所有轮次）
    chat_text = "\n".join([
        f"{'用户' if msg['role'] == 'user' else '系统'}: {msg['content']}"
        for msg in history
    ])

    prompt = f"""
        你是一个智能客服状态机。请根据以下完整对话，严格输出一个 JSON 对象，包含：
        - "scene": 主场景，必须是以下之一：logistics, complaint, refund, other
        - "status": 子状态，描述当前需要做什么或处于什么阶段

        规则：
        1. 如果用户首次提到物流，但未提到订单号 → scene=logistics, status=need_order_id
        2. 在用户提到物流后，判别订单号要注意以下几点：
        -如果用户提供的订单号符合6位数字格式 → scene=logistics, status=ready_to_query
        -如果用户提供的订单号不符合6位数字格式 → scene=logistics, status=invalid_order_id
        3. 如果用户提到物流，并已提供6位数字格式的订单号→ scene=logistics, status=ready_to_query
        4. 如果用户提到物流，并已提供订单号，但订单号不是6位数字格式→ scene=logistics, status=invalid_order_id
        5. 如果用户首次投诉，且未说明类型 → scene=complaint, status=need_type
        6. 如果用户投诉并已说明类型（如“服务差”、“商品问题”）→ scene=complaint, status=recorded
        7. 如果用户首次申请退款，且未说明原因 → scene=refund, status=need_reason
        8. 如果用户申请退款并已说明原因（如“质量差”、“不想要了”）→ scene=refund, status=processing
        9. 如果用户说“你好”等招呼语 → scene=other, status=greeting
        10. 其他情况 → scene=other, status=unknown

        请务必结合整个对话上下文判断当前所处流程！

        完整对话：
        {chat_text}

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
        if state.get("scene") not in {"logistics", "complaint", "refund", "other"}:
            state["scene"] = "other"
        return state
    except Exception as e:
        print(f"⚠️ Qwen 状态解析失败: {e}")
        return {"scene": "other", "status": "unknown"}
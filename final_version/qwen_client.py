# qwen_client.py
import os
import json
import re
from http import HTTPStatus
import dashscope

dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")

def call_qwen_with_state(user_input: str, history=None):

    system_prompt = (
    "你是一个电商客服意图解析器。请根据用户的**最新一句话**，判断其意图、状态，并提取关键信息。\n\n"
    
    "【输出要求】\n"
    "- 只输出一个 JSON 对象，不要任何其他文字、解释或 markdown。\n"
    "- JSON 必须包含三个字段：scene, status, slots\n\n"
    
    "【scene 取值】\n"
    "- logistics：用户提到查物流、快递、包裹、单号等\n"
    "- complaint：用户提到投诉、不满、服务差、商品问题等\n"
    "- refund：用户提到退款、退钱、不想买了、发错货等\n"
    "- other：其他情况\n\n"
    
    "【status 取值】\n"
    "- logistics: \n"
    "    • 如果用户**已经提供了订单号** → 'ready_to_query'\n"
    "    • 如果**没提供订单号** → 'need_order_id'\n"
    "    • 如果用户提供的订单号**格式不正确**（非6位数字）→ 'invalid_order_id'\n"
    "    • 当进入need_order_id时，如果用户提供的订单号**格式不正确**（非6位数字）→ 'invalid_order_id'\n"
    "- complaint:\n"
    "    • 如果用户**已经说明了投诉原因** → 'recorded'\n"
    "    • 如果**只说要投诉但没说原因** → 'need_type'\n"
    "- refund:\n"
    "    • 如果用户**已经说明了退款原因** → 'processing'\n"
    "    • 如果**只说要退款但没说原因** → 'need_reason'\n"
    "- other: 'greeting'（如你好/在吗） 或 'unknown'\n\n"
    
    "【slots 提取规则】\n"
    "- order_id：从句子中提取**连续的数字串**，作为订单号。没有则不填。\n"
    "- complaint_type：如果用户说了投诉原因（如“快递员态度差”），**原样摘录这句话的核心描述**。\n"
    "- refund_reason：如果用户说了退款原因（如“不想要了”），**原样摘录**。\n"
    "- 如果没有相关信息，slots 为 {}。\n\n"
    
    "【重要】\n"
    "- 不要猜测！只根据用户当前这句话判断。\n"
    "- 订单号必须是6位格式数字，字母不算（如 SF123 不提取）。\n\n"
    
    "【正确示例】\n"
    "用户输入：查一下我的快递，单号是888999\n"
    "输出：{\"scene\":\"logistics\",\"status\":\"ready_to_query\",\"slots\":{\"order_id\":\"888999\"}}\n\n"
    
    "用户输入：我要投诉\n"
    "输出：{\"scene\":\"complaint\",\"status\":\"need_type\",\"slots\":{}}\n\n"
    
    "用户输入：申请退款，因为发错货了\n"
    "输出：{\"scene\":\"refund\",\"status\":\"processing\",\"slots\":{\"refund_reason\":\"发错货了\"}}\n\n"
    
    "用户输入：你好\n"
    "输出：{\"scene\":\"other\",\"status\":\"greeting\",\"slots\":{}}\n\n"
    
    "现在请处理用户的最新输入："
)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input}
    ]

    response = dashscope.Generation.call(
        model='qwen-max',
        messages=messages,
        result_format='message'
    )

    if response.status_code != HTTPStatus.OK:
        raise RuntimeError(f"Qwen API Error: {response.code} - {response.message}")

    raw_text = response.output.choices[0].message.content.strip()

    # 尝试提取 JSON（兼容可能的 markdown 包裹）
    try:
        # 去掉 ```json ... ``` 包裹
        json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            result = json.loads(json_str)
        else:
            result = json.loads(raw_text)

        # 确保字段存在
        result.setdefault("scene", "other")
        result.setdefault("status", "unknown")
        result.setdefault("slots", {})
        return result

    except (json.JSONDecodeError, KeyError) as e:
        print(f"⚠️ Qwen 返回格式错误，使用默认状态。原始输出：{raw_text}")
        return {"scene": "other", "status": "unknown", "slots": {}}
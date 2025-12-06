# main.py
import asyncio
from lexer import Lexer
from parser import Parser
from interpreter import Interpreter, Context

dsl_code = '''
intent ask_order_for_logistics {
    match: llm_intent: "query_logistics"
    context: !has(order_id)
    actions: [
        ask("order_id", "请问您要查询哪个订单的物流信息？")
    ]
}

intent show_logistics {
    match: llm_intent: "query_logistics"
    context: has(order_id)
    actions: [
        call_api("logistics_service", {"order_id": "order_id"}),
        reply("正在为您查询订单 {{order_id}} 的物流信息...")
    ]
}

intent ask_complaint_type {
    match: llm_intent: "start_complaint" 
'''

async def main():
    # 解析 DSL
    lexer = Lexer(dsl_code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    program = parser.parse_program()

    interpreter = Interpreter(program)
    context = Context()

    print("💬 对话系统已启动（输入 'quit' 退出）")
    while True:
        user_input = input("\n👤 用户: ").strip()
        if user_input.lower() in ("quit", "exit"):
            break
        if not user_input:
            continue

        reply = await interpreter.run(user_input, context)
        print(f"🤖 系统: {reply}")

        # （可选）尝试从用户输入中提取 order_id（简单规则）
        if "订单" in user_input or user_input.isdigit():
            # 示例：假设用户直接输入了数字
            if user_input.isdigit():
                context.set("order_id", user_input)
            elif len(user_input) > 5:
                # 粗略提取长数字串作为订单号
                import re
                match = re.search(r"\d{6,}", user_input)
                if match:
                    context.set("order_id", match.group())

if __name__ == "__main__":
    asyncio.run(main())
# main.py
"""
DSL 多场景客服系统主程序
- 支持 refund / order_status / complaint 等脚本
- 使用 Qwen API 进行意图识别
- 加载 scripts/ 目录下的所有 .dsl 文件
"""

import os
from parser import DSLParser
from interpreter import Interpreter
from intent_recognition import recognize_intent


# ========================
# 模拟业务逻辑函数（实际项目中可替换为数据库/API调用）
# ========================
def check_refund(order_id: str) -> str:
    """模拟退款资格检查"""
    eligible_orders = {"1001", "1002", "1003"}
    return "eligible" if order_id in eligible_orders else "ineligible"


def get_order_status(order_id: str) -> str:
    """模拟订单状态查询"""
    statuses = {
        "1001": "已发货",
        "1002": "运输中",
        "1003": "已签收",
    }
    return statuses.get(order_id, "未找到该订单")


def create_ticket(complaint: str) -> str:
    """模拟创建工单，返回工单号"""
    # 实际项目中可存入数据库
    import time
    ticket_id = f"TKT{int(time.time())}"
    print(f"[DEBUG] 工单内容：{complaint}")  # 可选：调试用
    return ticket_id


# 注册所有可被 DSL 调用的函数
FUNCTIONS = {
    "check_refund": check_refund,
    "get_order_status": get_order_status,
    "create_ticket": create_ticket,
}


# ========================
# 主程序逻辑
# ========================
def load_scripts(scripts_dir: str = "scripts"):
    """加载 scripts/ 目录下所有 .dsl 脚本"""
    if not os.path.exists(scripts_dir):
        raise FileNotFoundError(f"脚本目录 '{scripts_dir}' 不存在，请创建并放入 .dsl 文件")

    script_cache = {}
    available_intents = []

    for filename in os.listdir(scripts_dir):
        if filename.endswith(".dsl"):
            intent_name = filename[:-4]  # 去掉 .dsl 后缀
            filepath = os.path.join(scripts_dir, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    source = f.read()
                parser = DSLParser(source)
                script = parser.parse()

                # 可选：校验 intent 名是否匹配文件名
                if script.intent != intent_name:
                    print(f"⚠️ 警告：文件 {filename} 声明的 intent 是 '{script.intent}'，但文件名为 '{intent_name}'")

                script_cache[intent_name] = script
                available_intents.append(intent_name)

            except Exception as e:
                print(f"❌ 加载脚本失败: {filepath} - {e}")
                continue

    if not available_intents:
        raise RuntimeError(f"未在 '{scripts_dir}/' 中找到任何有效的 .dsl 脚本！")

    return script_cache, available_intents


def main():
    print("🤖 欢迎使用 DSL 客服系统！")
    print("支持的业务场景：退款、查订单、投诉\n")

    try:
        script_cache, available_intents = load_scripts()
        print(f"✅ 已加载 {len(available_intents)} 个脚本: {available_intents}\n")
    except Exception as e:
        print(f"💥 初始化失败: {e}")
        return

    print("💡 示例输入：")
    print('   - "我想退货"')
    print('   - "查一下订单1001的状态"')
    print('   - "我要投诉快递员态度差"\n')

    while True:
        try:
            user_input = input("[用户] ").strip()
            if not user_input:
                continue

            if user_input.lower() in {"退出", "quit", "exit"}:
                print("👋 感谢使用，再见！")
                break

            # Step 1: 使用 Qwen 识别意图
            intent = recognize_intent(user_input, available_intents)
            print(f"[系统] 识别意图 → {intent}")

            if intent == "unknown":
                print("[Bot] 抱歉，我不太明白您的需求。您可以尝试说“退款”、“查订单”或“投诉”。\n")
                continue

            # Step 2: 执行对应脚本
            script = script_cache[intent]
            interpreter = Interpreter(script, functions=FUNCTIONS)
            interpreter.run()
            print()  # 空行分隔对话

        except KeyboardInterrupt:
            print("\n👋 程序被用户中断，再见！")
            break
        except Exception as e:
            print(f"[系统错误] {e}\n")


if __name__ == "__main__":
    main()
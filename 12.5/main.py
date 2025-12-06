# main.py
from parser import DSLParser
from interpreter import Interpreter

def check_refund(order_id: str) -> str:
    if order_id in ["1001", "1002", "1003"]:
        return "eligible"
    return "ineligible"

def main():
    dsl_text = (
        "intent: refund\n"
        "start:\n"
        "say \"请提供您的订单号（例如：1001）\"\n"
        "wait user_order_id\n"
        "if user_order_id == \"\":\n"
        "  say \"订单号不能为空！\"\n"
        "  goto start\n"
        "call check_refund(user_order_id) as eligibility\n"
        "if eligibility == \"eligible\":\n"
        "  say \"✅ 您可以申请退款。\"\n"
        "else:\n"
        "  say \"❌ 抱歉，该订单不符合退款条件。\"\n"
    )

    parser = DSLParser(dsl_text)
    script = parser.parse()

    functions = {"check_refund": check_refund}

    interpreter = Interpreter(script, functions)
    interpreter.run()

if __name__ == "__main__":
    main()
# test_parser.py
from parser import DSLParser
from ast import Script, LabelNode, SayNode, WaitNode, IfNode, CallNode

def test_refund_dsl():
    # 注意：if 块只包含一条语句！
    dsl_text = (
        "intent: refund\n"
        "start:\n"
        "say \"请提供订单号\"\n"
        "wait user_order_id\n"
        "if user_order_id == \"\":\n"
        "  say \"不能为空\"\n"          # ← 只保留这一条在 if 中
        "call check_refund(user_order_id) as eligibility"
    )
    
    parser = DSLParser(dsl_text)
    script = parser.parse()

    print(f"Parsed intent: {script.intent}")
    print(f"Statements count: {len(script.statements)}")
    for i, stmt in enumerate(script.statements):
        print(f"  [{i}] {type(stmt).__name__}")

    # 断言
    assert script.intent == "refund"
    assert len(script.statements) == 5
    assert isinstance(script.statements[0], LabelNode)
    assert script.statements[0].name == "start"
    assert isinstance(script.statements[1], SayNode)
    assert script.statements[1].message == "请提供订单号"

    print("✅ All tests passed!")

if __name__ == "__main__":
    test_refund_dsl()
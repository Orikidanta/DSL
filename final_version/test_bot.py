# test_bot.py
import sys
import os
import time
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr

# 确保能导入你的模块
sys.path.insert(0, os.path.dirname(__file__))

def run_conversation_real(user_inputs):
    """
    真实运行 main_v2，注入用户输入序列，捕获所有输出。
    不 mock 任何组件，包括 Qwen。
    """
    inputs = iter(user_inputs)
    
    def mock_input(prompt=""):
        try:
            value = next(inputs)
            # 可选：打印用户输入便于观察
            # print(f"👤 用户: {value}", file=sys.__stdout__)
            return value
        except StopIteration:
            return 'q'  # 自动退出
    
    output = StringIO()
    with redirect_stdout(output), redirect_stderr(output):
        original_input = input
        __builtins__.input = mock_input
        try:
            from main import main_v2
            main_v2()
        finally:
            __builtins__.input = original_input
    
    return output.getvalue()


def test_case(name, user_inputs, expected_substrings):
    print(f"\n🧪 测试用例: {name}")
    print("-" * 50)
    
    # 给 LLM 调用留出时间（避免速率限制）
    time.sleep(1)
    
    actual_output = run_conversation_real(user_inputs)
    
    success = True
    for expected in expected_substrings:
        if expected not in actual_output:
            print(f"❌ 未找到预期内容: '{expected}'")
            success = False
    
    if success:
        print("✅ 通过")
    else:
        print("⚠️ 实际完整输出:")
        print(actual_output)
    return success


def main():
    all_passed = True

    # === 一步到位场景 ===
    all_passed &= test_case(
        "物流 - 一句话带订单号",
        ["查物流，订单号是123456"],
        ["正在查询 123456 的物流信息..."]
    )

    all_passed &= test_case(
        "投诉 - 一句话带原因",
        ["我要投诉快递员态度恶劣"],
        ["已记录您的 快递员态度恶劣 投诉"]
    )

    all_passed &= test_case(
        "退款 - 一句话带原因",
        ["申请退款，商品和描述不符"],
        ["正在处理您的退款申请..."]
    )

    # === 传统分步流程（确保基础功能没坏）===
    all_passed &= test_case(
        "物流 - 分步输入",
        ["物流", "789012"],
        ["请问您的订单号是？", "正在查询 789012 的物流信息..."]
    )

    all_passed &= test_case(
        "未知意图",
        ["今天心情不好"],
        ["我不太确定您的需求，请说明是要查物流、投诉还是退款？"]
    )

    # === 退出重置测试 ===
    all_passed &= test_case(
        "退出后重置",
        ["物流", "123", "退出", "你好"],
        [   
            "请问您的订单号是？",
            "您再确定一下订单号,这里没查到你的订单",
            "用户退出会话，系统已重置状态",
            "您好！请问是要查物流、投诉还是退款？",
            "您好请问有什么可以帮到你的吗？我可以为您查物流，同时负责投诉和退款问题呢"
        ]
    )

    print("\n" + "="*60)
    if all_passed:
        print("🎉 所有端到端测试通过！")
    else:
        print("💥 部分测试失败。")
    print("="*60)


if __name__ == "__main__":
    main()
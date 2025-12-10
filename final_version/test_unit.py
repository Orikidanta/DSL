# test_unit.py
import sys
import os
import unittest
from unittest.mock import patch
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr

# 将当前目录加入模块搜索路径，以便导入项目模块
sys.path.insert(0, os.path.dirname(__file__))


def run_conversation_with_mock(user_inputs, mock_return_value):
    """
    模拟一次完整的对话流程，使用 mock 替代 Qwen 调用。
    每次调用前会清空全局 context，确保测试隔离。
    """
    inputs = iter(user_inputs)
    
    def fake_input(prompt=""):
        try:
            return next(inputs)
        except StopIteration:
            return 'q'  # 安全退出

    output = StringIO()
    
    with redirect_stdout(output), redirect_stderr(output):
        # 替换内置 input 函数
        original_input = __builtins__.input
        __builtins__.input = fake_input

        try:
            # 关键：导入并清空 main 中的全局 context
            from main import context
            context.clear()  # 清除上一次测试残留数据

            # 打补丁：替换 LLM 调用为预设返回值
            with patch('qwen_client.call_qwen_with_state', return_value=mock_return_value):
                from main import main_v2
                main_v2()

        finally:
            # 恢复原始 input
            __builtins__.input = original_input

    return output.getvalue()


class TestCustomerServiceWithStubs(unittest.TestCase):
    """基于测试桩（stub）的单元测试，完全隔离外部依赖"""

    def test_logistics_one_shot(self):
        """一句话查物流（带订单号）"""
        mock_output = {
            "scene": "logistics",
            "status": "ready_to_query",
            "slots": {"order_id": "888999"}
        }
        result = run_conversation_with_mock(
            user_inputs=["查物流，订单号888999"],
            mock_return_value=mock_output
        )
        self.assertIn("正在查询 888999 的物流信息...", result)

    def test_complaint_with_reason(self):
        """投诉并说明原因"""
        mock_output = {
            "scene": "complaint",
            "status": "recorded",
            "slots": {"complaint_type": "快递员态度差"}
        }
        result = run_conversation_with_mock(
            user_inputs=["我要投诉快递员态度差"],
            mock_return_value=mock_output
        )
        self.assertIn("已记录您的 快递员态度差 投诉", result)

    def test_refund_with_reason(self):
        """退款并说明原因"""
        mock_output = {
            "scene": "refund",
            "status": "processing",
            "slots": {"refund_reason": "发错货了"}
        }
        result = run_conversation_with_mock(
            user_inputs=["申请退款，发错货了"],
            mock_return_value=mock_output
        )
        self.assertIn("正在处理您的退款申请...", result)

    def test_logistics_need_order_id(self):
        """只提物流，未提供订单号 → 应追问"""
        mock_output = {
            "scene": "logistics",
            "status": "need_order_id",
            "slots": {}
        }
        result = run_conversation_with_mock(
            user_inputs=["我想查物流"],
            mock_return_value=mock_output
        )
        self.assertIn("请问您的订单号是？", result)

    def test_complaint_need_type(self):
        """只说“投诉”，未说明原因 → 应追问"""
        mock_output = {
            "scene": "complaint",
            "status": "need_type",
            "slots": {}
        }
        result = run_conversation_with_mock(
            user_inputs=["我要投诉"],
            mock_return_value=mock_output
        )
        self.assertIn("请问投诉类型？", result)

    def test_unknown_intent(self):
        """未知意图 → 兜底回复"""
        mock_output = {
            "scene": "other",
            "status": "unknown",
            "slots": {}
        }
        result = run_conversation_with_mock(
            user_inputs=["今天天气怎么样？"],
            mock_return_value=mock_output
        )
        self.assertIn("我不太确定您的需求", result)

    def test_greeting(self):
        """问候语识别"""
        mock_output = {
            "scene": "other",
            "status": "greeting",
            "slots": {}
        }
        result = run_conversation_with_mock(
            user_inputs=["你好"],
            mock_return_value=mock_output
        )
        self.assertIn("您好请问有什么可以帮到你的吗？我可以为您查物流，同时负责投诉和退款问题呢", result)


if __name__ == '__main__':
    # 运行所有单元测试
    unittest.main(verbosity=2)
# 意图标识：该脚本响应 "refund" 意图
intent: refund

# 入口标签
start:
  say "您好！请提供您要申请退款的订单编号（例如：ORD12345）。"
  wait user_order_id

  # 检查用户是否输入了内容
  if user_order_id == "":
    say "订单编号不能为空，请重新输入。"
    goto start

  # 调用外部服务检查退款资格（模拟）
  call check_refund_eligibility(user_order_id) as eligibility

  if eligibility == "eligible":
    say "您的订单 ${user_order_id} 符合退款条件。"
    call process_refund(user_order_id)
    say "退款已提交，预计3-5个工作日到账。感谢您的理解！"
  elif eligibility == "not_found":
    say "未找到订单 ${user_order_id}，请确认编号是否正确。"
    goto start
  else:  # e.g., "ineligible"
    say "很抱歉，订单 ${user_order_id} 不符合退款政策（如已超过7天）。"
    say "如有疑问，请联系人工客服。"
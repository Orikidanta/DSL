intent: refund
start:
say "请提供订单号以便处理退款"
wait user_order_id
if user_order_id == "":
  say "订单号不能为空！"
  goto start
call check_refund(user_order_id) as eligibility
if eligibility == "eligible":
  say "✅ 您的订单符合退款条件，正在处理中…"
else:
  say "❌ 抱歉，该订单暂不支持退款。"
intent: order_status
ask:
say "请输入订单号查询物流"
wait order_id
if order_id == "":
  say "订单号不能为空！"
  goto ask
call get_order_status(order_id) as status
say "📦 当前状态：{status}"
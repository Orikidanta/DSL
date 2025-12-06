intent: complaint
begin:
say "请描述您遇到的问题"
wait user_complaint
if user_complaint == "":
  say "问题描述不能为空！"
  goto begin
call create_ticket(user_complaint) as ticket
say "📝 工单 {ticket} 已提交，客服将在24小时内联系您。"
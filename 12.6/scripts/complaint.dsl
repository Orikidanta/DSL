intent handle_complaint {
    match: llm_intent: "make_complaint"
    context: has(complaint_detail) && has(order_id)
    actions: [
        call_api("complaint_service", {
            order_id: ctx.order_id,
            complaint: ctx.complaint_detail,
            user_id: ctx.user_id
        }),
        if (api_result.ticket_id) {
            reply("您的投诉已提交，工单号为 {{api_result.ticket_id}}，我们将在24小时内联系您。")
        } else {
            llm_reply("很抱歉给您带来不便。{{complaint_detail}} 我们已记录您的反馈，并会尽快处理。")
        }
    ]
}

intent ask_complaint_detail {
    match: llm_intent: "make_complaint"
    context: has(order_id) && !has(complaint_detail)
    actions: [
        ask("complaint_detail", "请您详细描述遇到的问题，我们会尽快为您处理。"),
        goto(handle_complaint)
    ]
}

intent ask_order_for_complaint {
    match: llm_intent: "make_complaint"
    context: !has(order_id)
    actions: [
        ask("order_id", "为了更好地帮助您，请提供相关订单号。"),
        goto(ask_complaint_detail)
    ]
}
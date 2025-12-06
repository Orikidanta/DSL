intent process_refund {
    match: llm_intent: "request_refund"
    context: has(order_id) && has(refund_reason)
    actions: [
        call_api("refund_service", {
            order_id: ctx.order_id,
            reason: ctx.refund_reason,
            user_id: ctx.user_id
        }),
        switch (api_result.status) {
            case "approved":
                reply("您的退款申请已通过，预计3-5个工作日内到账。")
            case "pending_review":
                reply("您的退款申请已提交，正在审核中，请耐心等待。")
            default:
                llm_reply("很抱歉，当前无法处理您的退款请求。原因：{{api_result.message}}。如有疑问，请联系人工客服。")
        }
    ]
}

intent ask_refund_reason {
    match: llm_intent: "request_refund"
    context: has(order_id) && !has(refund_reason)
    actions: [
        ask("refund_reason", "请问您申请退款的原因是什么？（如：商品损坏、发错货、不想要了等）"),
        goto(process_refund)
    ]
}

intent ask_order_for_refund {
    match: llm_intent: "request_refund"
    context: !has(order_id)
    actions: [
        ask("order_id", "请提供您要申请退款的订单号。"),
        goto(ask_refund_reason)
    ]
}
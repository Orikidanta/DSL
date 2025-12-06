intent logistics_query {
    match: llm_intent: "query_logistics"
    context: has(order_id)
    actions: [
        call_api("logistics_service", { order_id: ctx.order_id }),
        if (api_result.success) {
            reply("您的订单 {{order_id}} 当前物流状态：{{api_result.status}}，最新更新时间：{{api_result.update_time}}。")
        } else {
            reply("抱歉，暂时无法查询到该订单的物流信息，请稍后再试。")
        }
    ]
}

intent ask_order_for_logistics {
    match: llm_intent: "query_logistics"
    context: !has(order_id)
    actions: [
        ask("order_id", "请问您要查询哪个订单的物流信息？请提供订单号。"),
        goto(logistics_query)
    ]
}
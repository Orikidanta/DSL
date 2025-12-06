# example.py
from lexer import Lexer
from parser import Parser

dsl_code = '''
intent ask_order_for_logistics {
    match: llm_intent: "query_logistics"
    context: !has(order_id)
    actions: [
        ask("order_id", "请问您要查询哪个订单的物流信息？"),
        goto(logistics_query)
    ]
}
'''

if __name__ == "__main__":
    lexer = Lexer(dsl_code)
    tokens = lexer.tokenize()
    print("Tokens:", [(t.type.name, t.value) for t in tokens if t.type.name != 'EOF'])

    parser = Parser(tokens)
    program = parser.parse_program()
    print("\nParsed AST:")
    for intent in program.intents:
        print(f"- Intent: {intent.name}")
        print(f"  Match: {intent.match}")
        print(f"  Context: {intent.context}")
        print(f"  Actions: {len(intent.actions)} item(s)")
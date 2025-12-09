# main.py

import json
from qwen_client import call_qwen_with_state  # 假设你的 Qwen 接口返回 (scene, status)
from dsl_loader import load_dsl
from context import Context

EXIT_KEYWORDS = {'退出', 'quit', 'exit', '返回'}

# ==============================
# 更健壮的版本：使用 pending_field
# ==============================

def main_v2():
    with open('rules.txt', encoding='utf-8') as f:
        rules = load_dsl(f.read())

    context = Context()
    history = []
    pending_field = None  # 记录下一个用户输入要填充的字段

    print("🤖 客服机器人 v2 启动！\n")
    
    while True:
        user_input = input("👤 用户: ").strip()
        
        if user_input in {'退出', 'quit'}:
            call_qwen_with_state(None, None)  # 清空状态
            history.clear()
            context.clear()
            print("已退出。")
            continue

        history.append({"role": "user", "content": user_input})

        state = call_qwen_with_state(user_input, history)
        scene, status = state.get("scene"), state.get("status")
        print(f"🔍 当前状态: {scene} / {status}")

        # 如果有待填字段，直接存入上下文
        if pending_field:
            context.set(pending_field, user_input)
            print(f"✅ 已记录: {pending_field} = {user_input}")
            pending_field = None  # 清除
            # 注意：即使存了字段，也要把用户输入加入 history，供 Qwen 参考
            history.append({"role": "user", "content": user_input})
        else:
            history.append({"role": "user", "content": user_input})

        # 调用 Qwen 判断当前状态
        scene, status = state.get("scene"), state.get("status")
        print(f"🔍 Qwen: scene='{scene}', status='{status}'")

        matched = False
        for rule in rules:
            if rule.get('scene') == scene and rule.get('status') == status:
                matched = True
                for action in rule['actions']:
                    if action['type'] == 'ask':
                        field = action['field']
                        prompt = action.get('prompt', f"请输入 {field}：")
                        print(f"💬 系统: {prompt}")
                        history.append({"role": "assistant", "content": prompt})
                        pending_field = field  # 标记下一个输入是这个字段
                        break
                    elif action['type'] == 'reply':
                        msg = context.render(action['message'])
                        print(f"💬 系统: {msg}")
                        history.append({"role": "assistant", "content": msg})
                break

        if not matched:
            msg = "我不太确定您的需求，请说明是要查物流、投诉还是退款？"
            print(f"💬 系统: {msg}")
            history.append({"role": "assistant", "content": msg})


if __name__ == '__main__':
    # 使用更健壮的 v2 版本
    main_v2()
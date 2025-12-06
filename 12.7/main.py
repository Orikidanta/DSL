# main.py
from dsl_loader import load_dsl
from qwen_client import call_qwen_with_state
import re

class SimpleContext:
    def __init__(self):
        self.data = {}
    def set(self, k, v): self.data[k] = v
    def render(self, t): return re.sub(r'\{\{(\w+)\}\}', lambda m: self.data.get(m.group(1), m.group(0)), t)

def main():
    with open('rules.txt', encoding='utf-8') as f:
        rules = load_dsl(f.read())
        
    context = SimpleContext()
    history = []

    print("🤖 客服机器人（Qwen 状态驱动）")
    while True:
        user_input = input("\n用户: ").strip()
        if user_input.lower() in ('quit', 'exit','再见'):
            break

        # 调 Qwen 获取 (scene, status)
        state = call_qwen_with_state(user_input, history)
        scene = state.get("scene", "other")
        status = state.get("status", "unknown")
        print(f"🔍 Qwen 状态: scene={scene}, status={status}")

        # 匹配规则
        print(f"🔍 Qwen: scene='{scene}', status='{status}' (类型: {type(scene)}, {type(status)})")
        print(f"🔍 规则数量: {len(rules)}")

        matched = False
        for i, rule in enumerate(rules):
            rule_scene = rule.get('scene', 'MISSING')
            rule_status = rule.get('status', 'MISSING')
            
            
            
            # 强制转换为字符串并比较
            scene_ok = str(rule_scene).strip().lower() == str(scene).strip().lower()
            status_ok = str(rule_status).strip().lower() == str(status).strip().lower()
            
            if scene_ok and status_ok:
                print(f"🎯 匹配成功！规则 {i}")
                matched = True
                print(f"🔍 actions 数量: {len(rule['actions'])}")
                for action in rule['actions']:
                    print(f"🔍 actions 数量: {len(rule['actions'])}")
                    if action['type'] == 'ask':
                        print(f"🤖 {action['prompt']}")
                        input("用户: ")
                    elif action['type'] == 'reply':
                        print(f"系统: {action['message']}")
                break
            else:
                print(f"  → 不匹配: scene_ok={scene_ok}, status_ok={status_ok}")

        if not matched:
            print("❌ 未找到匹配规则")



if __name__ == '__main__':
    main()
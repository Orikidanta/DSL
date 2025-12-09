# context.py
class Context:
    def __init__(self):
        self.data = {}

    def set(self, key, value):
        self.data[key] = value

    def render(self, text):
        # 支持 {{order_id}} 替换
        from string import Template
        # 使用 safe_substitute 避免 KeyError
        template = Template(text)
        return template.safe_substitute(self.data)
    
    def clear(self):
        """清空所有上下文变量"""
        self.data.clear()
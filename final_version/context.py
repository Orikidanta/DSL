# context.py
class Context:
    def __init__(self):
        self.data = {}

    def set(self, key, value):
        self.data[key] = value

    def clear(self):
        self.data.clear()  # 👈 添加这一行！

    def render(self, text):
        result = text
        for key, value in self.data.items():
            placeholder1 = f"{{{{{key}}}}}"
            result = result.replace(placeholder1, str(value))
            if '/' in key:
                alias_key = key.replace('/', '_')
                placeholder2 = f"{{{{{alias_key}}}}}"
                result = result.replace(placeholder2, str(value))
        return result
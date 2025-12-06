# context.py
import re

class Context:
    def __init__(self):
        self.current_flow = None
        self.data = {}

    def has(self, field: str) -> bool:
        return field in self.data

    def set(self, field: str, value: str):
        self.data[field] = value.strip()

    def render(self, template: str) -> str:
        def replace_match(m):
            key = m.group(1)
            return self.data.get(key, f"{{{{{key}}}}}")
        return re.sub(r'\{\{(\w+)\}\}', replace_match, template)
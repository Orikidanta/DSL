#dsl_loader.py

def load_dsl(dsl_text: str):
    rules = []
    current = None
    for line in dsl_text.strip().split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        if line.startswith('[') and line.endswith(']'):
            section = line[1:-1].strip()
            current = {'type': section, 'scene': None, 'status': None, 'actions': []}
            rules.append(current)
            continue

        if ':' not in line or current is None:
            continue

        key, val = line.split(':', 1)
        key, val = key.strip(), val.strip()

        if key in ('scene', 'status'):
            current[key] = val
        elif key == 'ask':
            current['actions'].append({'type': 'ask', 'field': val})
        elif key == 'prompt':
            current['actions'][-1]['prompt'] = val
        elif key == 'reply':
            current['actions'].append({'type': 'reply', 'message': val})

    return rules
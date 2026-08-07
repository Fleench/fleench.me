import os
import re

def fix_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    def replacer(m):
        indent = m.group(1)
        return f'{indent}with Element("div", {{"style": "display:none;"}}):\n{indent}    api["methods"]["foot"]()'
    
    # Replace ONLY if it's not already fixed
    if 'with Element("div", {"style": "display:none;"}):' not in content:
        content = re.sub(r'^([ \t]+)api\["methods"\]\["foot"\]\(\)', replacer, content, flags=re.MULTILINE)

    with open(filepath, 'w') as f:
        f.write(content)

for root, _, files in os.walk('src'):
    for f in files:
        if f.endswith('.ghtml'):
            fix_file(os.path.join(root, f))

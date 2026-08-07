import os
import re

def fix_file_v2(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Match: (spaces)api["methods"]["foot"]()...(spaces)return page
    pattern = re.compile(r'(\s+)api\["methods"\]\["foot"\]\(\)(.*?)\s+return page', re.DOTALL)
    
    def replacer(match):
        orig_indent = match.group(1)
        block = 'page.add(api["methods"]["foot"]())' + match.group(2)
        
        # Dedent the block to 4 spaces
        lines = block.split('\n')
        new_lines = []
        for line in lines:
            if line.startswith(orig_indent):
                new_lines.append('    ' + line[len(orig_indent):])
            elif line.strip() == '':
                new_lines.append('')
            else:
                # If it has less indent, just strip and add 4 spaces
                new_lines.append('    ' + line.lstrip())
                
        return '\n\n' + '\n'.join(new_lines) + '\n    return page'
        
    new_content = pattern.sub(replacer, content)
    
    with open(filepath, 'w') as f:
        f.write(new_content)

for root, _, files in os.walk('src'):
    for f in files:
        if f.endswith('.ghtml') and f != 'index.ghtml':
            fix_file_v2(os.path.join(root, f))

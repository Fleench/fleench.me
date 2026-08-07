import os

def fix_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # Case 1: title = page.find... \n title.add(...)
    # Replace `title.add(Text(context["title"]))` with `with title:\n                        Text(context["title"])`
    # We need to match the indentation.
    import re
    
    def replacer1(m):
        indent = m.group(1)
        return f'{indent}with title:\n{indent}    Text(context["title"])'
    
    content = re.sub(r'^([ \t]+)title\.add\(Text\(context\["title"\]\)\)', replacer1, content, flags=re.MULTILINE)
    
    # Case 2: page.find("tag", "title")[0].add(Text(context["title"]))
    def replacer2(m):
        indent = m.group(1)
        return f'{indent}with page.find("tag", "title")[0]:\n{indent}    Text(context["title"])'
        
    content = re.sub(r'^([ \t]+)page\.find\("tag", "title"\)\[0\]\.add\(Text\(context\["title"\]\)\)', replacer2, content, flags=re.MULTILINE)

    with open(filepath, 'w') as f:
        f.write(content)

for root, _, files in os.walk('src'):
    for f in files:
        if f.endswith('.ghtml'):
            fix_file(os.path.join(root, f))

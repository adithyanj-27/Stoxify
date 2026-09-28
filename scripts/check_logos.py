import os
import re

with open('static/app.js', 'r', encoding='utf-8') as f:
    content = f.read()

m = re.search(r'const LOCAL_LOGOS = new Set\(\[(.*?)\]\);', content, re.DOTALL)
items = set()
if m:
    for token in re.findall(r'"([^"]+)"', m.group(1)):
        items.add(token)

existing = set(f[:-4] for f in os.listdir('static/logos') if f.endswith('.png'))
print(f"In app.js: {len(items)}")
print(f"On disk: {len(existing)}")
print(f"On disk but not in app.js: {sorted(list(existing - items))}")
print(f"In app.js but not on disk: {sorted(list(items - existing))}")

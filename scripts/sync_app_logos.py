import os
import re

files = sorted([f[:-4] for f in os.listdir('static/logos') if f.endswith('.png')])
print(f"Total logos in static/logos: {len(files)}")

with open('static/app.js', 'r', encoding='utf-8') as f:
    content = f.read()

formatted_items = ',\n  '.join(
    ', '.join(f'"{item}"' for item in files[i:i+10])
    for i in range(0, len(files), 10)
)
replacement = f'const LOCAL_LOGOS = new Set([\n  {formatted_items}\n]);'

new_content = re.sub(r'const LOCAL_LOGOS = new Set\(\[\s*[\s\S]*?\s*\]\);', replacement, content)

with open('static/app.js', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Updated LOCAL_LOGOS in static/app.js successfully!")

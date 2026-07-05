import re

with open('web/app.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'statsRow' in line:
        print(f"statsRow match: {i+1}: {line.strip()}")
    if 'dataset-meta' in line or 'dataset info' in line or 'stats-row' in line:
        print(f"dataset info match: {i+1}: {line.strip()}")

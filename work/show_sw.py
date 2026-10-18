import re, os
sw = open("sw.js", encoding="utf-8").read()
print("=== sw.js 中的 ASSETS 段 ===")
m = re.search(r"ASSETS\s*=\s*\[(.*?)\]", sw, re.S)
print(m.group(0)[:900] if m else "（未找到 ASSETS）")
print("\n=== sw.js 全文（前 60 行）===")
for i, l in enumerate(sw.split("\n")[:60], 1):
    print(f"{i:3d}: {l}")

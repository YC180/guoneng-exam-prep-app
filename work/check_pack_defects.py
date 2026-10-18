import csv, re
from collections import Counter
p = r"D:\DOWNLOADS\app\可选导入\专业知识练习题_计算机类.csv"
rows = list(csv.reader(open(p, encoding="utf-8")))
data = [r for r in rows if r and r[0].startswith("zy-jsj-")]
print("题数:", len(data))
c = Counter()
for r in data:
    s = r[2]
    if "【解析】" in s: c["题干含【解析】（解析尾巴混入）"] += 1
    if re.match(r"^\s*\d+[.、]", s): c["题干保留题号"] += 1
    if s.endswith("(") or s.endswith("（"): c["题干尾部残留括号"] += 1
    if len(re.sub(r"\s","",s)) < 10: c["题干过短(<10字)"] += 1
    if "解析" in (r[8] or "") : c["有解析"] += 1
for k,v in c.most_common(): print(f"  {k}: {v}")
print("\n题干含【解析】的样例：")
for r in data:
    if "【解析】" in r[2]:
        print("  -", r[2][:100]); break
print("\n解析列非空占比:", sum(1 for r in data if (r[8] or '').strip()), "/", len(data))

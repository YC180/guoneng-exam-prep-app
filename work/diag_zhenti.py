import json, re
from collections import Counter, defaultdict
qs = json.load(open("bank/questions.json", encoding="utf-8"))["questions"]
zz = [q for q in qs if q.get("category") == "历年真题"]
print("历年真题类合计:", len(zz), "题；来源文件", len({q.get("sourceFile") for q in zz}), "个")
by = defaultdict(int)
for q in zz:
    s = q.get("sourceFile") or ""
    m = re.match(r"(\d{4})", s)
    by[m.group(1) if m else "其他"] += 1
for y, n in sorted(by.items()):
    print(f"  {y}: {n} 题")
print("\n题型:", dict(Counter(q.get("type") for q in zz)))
mo = [q for q in qs if q.get("category") == "模拟笔试"]
print("\n模拟笔试类:", len(mo), "题；来源", len({q.get("sourceFile") for q in mo}), "个")
for s, n in Counter(q.get("sourceFile") for q in mo).most_common():
    print(f"  {n:4d}  {s}")

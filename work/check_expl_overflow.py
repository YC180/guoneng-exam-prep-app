import json, re
from collections import Counter
qs = json.load(open("bank/questions.json", encoding="utf-8"))["questions"]
OVF = re.compile(r"\d{1,3}\s*[.、]?\s*【\s*答\s*案\s*】")
bad = [q for q in qs if OVF.search(q.get("explanation") or "")]
print(f"解析里混进下一题答案标记的题：{len(bad)} / {len(qs)}")
print("按来源分布（前 8）：")
for s, n in Counter(q.get("sourceFile","") for q in bad).most_common(8):
    print(f"  {n:5d}  {s}")
print("\n样例：")
for q in bad[:3]:
    e = q.get("explanation") or ""
    m = OVF.search(e)
    print(f"  来源 {q.get('sourceFile','')[:40]}")
    print(f"    解析末尾溢出片段：「{e[m.start():m.start()+70]}」")
# 超长解析
long_e = [q for q in qs if len(q.get("explanation") or "") > 800]
print(f"\n解析超过 800 字的题：{len(long_e)}")

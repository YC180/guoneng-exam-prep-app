import json, os
from collections import Counter
qs = json.load(open("bank/questions.json", encoding="utf-8"))["questions"]
bad = [q for q in qs if len(q.get("options") or []) > 8]
print("选项数 >8 的题:", len(bad))
c = Counter(q.get("sourceFile", "?") for q in bad)
for f, n in c.most_common(12):
    print(f"  {n:4d}  {f}")
print()
for q in sorted(bad, key=lambda x: -len(x.get("options") or []))[:3]:
    print("选项数", len(q["options"]), "| 来源", q.get("sourceFile"))
    print("  题干:", (q.get("stem") or "")[:160])
    print("  前3选项:", [o.get("text", "")[:30] for o in q["options"][:3]])
    print()

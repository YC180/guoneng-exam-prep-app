import json
from collections import Counter
qs = json.load(open("bank/questions.json", encoding="utf-8"))["questions"]
def keys_of(q):
    return [str(o.get("key") or "").strip().upper() for o in (q.get("options") or [])]
def ans_of(q):
    return [str(a).strip().upper() for a in (q.get("answer") or []) if str(a).strip()]

bug = Counter()
srcs = Counter()
for q in qs:
    if q.get("answerStatus") != "verified":
        continue
    ks, ans = keys_of(q), ans_of(q)
    kset = {k for k in ks if k}
    dup = any(n > 1 for n in Counter(k for k in ks if k).values())
    if not ans:
        bug["verified但无答案"] += 1; srcs[(q.get("sourceFile") or "?")[:44]] += 1
    elif any(a not in kset for a in ans):
        bug["verified但答案越界"] += 1; srcs[(q.get("sourceFile") or "?")[:44]] += 1
    elif len(ks) < 2:
        bug["verified但选项<2"] += 1; srcs[(q.get("sourceFile") or "?")[:44]] += 1
    elif dup:
        bug["verified但选项键重复"] += 1; srcs[(q.get("sourceFile") or "?")[:44]] += 1
print("仍标为 verified 却结构不自洽的题：")
for k, v in bug.most_common():
    print(f"  {k:22s} {v}")
print("  合计", sum(bug.values()))
print("\n来源分布:")
for k, v in srcs.most_common(8):
    print(f"  {v:4d}  {k}")
print("\n题型分布:", Counter(q.get("type") for q in qs
      if q.get("answerStatus") == "verified"
      and (not ans_of(q) or any(a not in {k for k in keys_of(q) if k} for a in ans_of(q))
           or len(keys_of(q)) < 2
           or any(n > 1 for n in Counter(k for k in keys_of(q) if k).values()))).most_common())

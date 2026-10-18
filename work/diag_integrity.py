import json
from collections import Counter
qs = {q["id"]: q for q in json.load(open("bank/questions.json", encoding="utf-8"))["questions"]}
for qid in ("q02259", "q02557", "q02238"):
    q = qs[qid]
    print(f"=== {qid} type={q.get('type')} answer={q.get('answer')} status={q.get('answerStatus')}")
    print("   题干:", (q.get("stem") or "")[:110])
    print("   选项:", [(o.get("key"), (o.get("text") or "")[:28]) for o in (q.get("options") or [])])
    print("   来源:", (q.get("sourceFile") or "")[:70], "页", q.get("sourcePage"))
    print()
# 统计“答案越界”的选项个数分布
bad = []
for q in qs.values():
    keys = {str(o.get("key") or "").strip().upper() for o in (q.get("options") or [])}
    ans = [str(a).strip().upper() for a in (q.get("answer") or []) if str(a).strip()]
    if any(a not in keys for a in ans):
        bad.append((q, len(q.get("options") or []), len(keys)))
print("答案越界题数:", len(bad))
print("其中选项数为0的:", sum(1 for _, n, _ in bad if n == 0))
print("选项数分布:", Counter(n for _, n, _ in bad).most_common(8))
print("题型分布:", Counter(q.get("type") for q, _, _ in bad).most_common())
print("来源分布:", Counter((q.get("sourceFile") or "?")[:46] for q, _, _ in bad).most_common(6))

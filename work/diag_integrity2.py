import json
from collections import Counter
qs = json.load(open("bank/questions.json", encoding="utf-8"))["questions"]
shown = Counter()
for q in qs:
    opts = q.get("options") or []
    keys = [str(o.get("key") or "").strip().upper() for o in opts]
    ans = [str(a).strip().upper() for a in (q.get("answer") or []) if str(a).strip()]
    if not any(a not in {k for k in keys if k} for a in ans):
        continue
    n = len(opts)
    if n == 0 or shown[n] >= 3:
        continue
    shown[n] += 1
    print(f"--- 选项数={n} type={q.get('type')} answer={ans} status={q.get('answerStatus')}")
    print("   题干:", (q.get("stem") or "")[:100].replace("\n", " "))
    print("   选项:", [(o.get("key"), (o.get("text") or "")[:24]) for o in opts])
    print("   来源:", (q.get("sourceFile") or "")[:60])
    print()
print("按选项数取样:", dict(shown))

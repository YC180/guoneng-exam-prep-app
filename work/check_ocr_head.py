import json, re
qs = json.load(open("bank/questions.json", encoding="utf-8"))["questions"]
pat = re.compile(r"^\s*#|#\s*OCR|#\s*SOURCE|\[\[PAGE")
hits = [q for q in qs if pat.search(q.get("stem") or "")]
print("主题库中含 OCR/元信息头污染的题:", len(hits), "/", len(qs))
from collections import Counter
print("按来源文件:", Counter(q.get("sourceFile") for q in hits).most_common(8))
for q in hits[:6]:
    print(f"  [{q['answerStatus']}] {q['sourceFile'][:38]:38s} | {(q['stem'] or '')[:70]}")
# 选项里是否也被污染
oh = [q for q in qs if any(pat.search(o.get('text') or '') for o in q.get('options') or [])]
print("\n选项被污染的题:", len(oh))
# 解析字段
eh = [q for q in qs if pat.search(q.get("explanation") or "")]
print("解析被污染的题:", len(eh))

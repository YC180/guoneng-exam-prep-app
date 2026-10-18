import json, os
from collections import Counter
qs = json.load(open("bank/questions.json", encoding="utf-8"))["questions"]
st = Counter(q.get("answerStatus") for q in qs)
cat = Counter(q.get("category") for q in qs)
ocr = sum(1 for q in qs if "OCR" in (q.get("tags") or []))
qa = json.load(open("bank/quality_audit.json", encoding="utf-8"))
cov = json.load(open("bank/read_coverage.json", encoding="utf-8"))
kinds = Counter(r["kind"] for r in cov)
noexp = sum(1 for q in qs if not (q.get("explanation") or "").strip())
print(f"总量 {len(qs)} | 已核对 {st['verified']} | 待核对 {st['needs_review']} | 无答案 {st['missing']}")
print(f"OCR题 {ocr} | 无解析 {noexp} | 结构问题 {qa['flagged']} ({qa['rate']*100:.1f}%) → 结构完整 {len(qs)-qa['flagged']}")
print("类别:", dict(cat))
print("覆盖:", dict(kinds), "总计", len(cov))
app = r"D:\DOWNLOADS\app"
print("questions.js:", round(os.path.getsize(os.path.join(app,"data","questions.js"))/1024/1024,2), "MB")
print("docs 份数:", len(os.listdir(os.path.join(app,"docs"))))

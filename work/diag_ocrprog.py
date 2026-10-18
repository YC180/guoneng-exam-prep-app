import json, os
from collections import Counter
p = r"D:\app project\work\ocr\manifest.json"
print("manifest 存在:", os.path.exists(p))
if os.path.exists(p):
    m = json.load(open(p, encoding="utf-8"))
    recs = m if isinstance(m, list) else (m.get("files") or m.get("records") or list(m.values()))
    if recs and not isinstance(recs[0], dict):
        recs = []
    c = Counter((r.get("status") or "?") for r in recs if isinstance(r, dict))
    print(f"  条目 {len(recs)}；状态 {dict(c)}")
    pend = [r for r in recs if isinstance(r, dict) and (r.get("status") or "") not in ("done","ok","skipped")]
    print(f"  未完成 {len(pend)}：")
    for r in pend[:16]:
        print("    " + str(r.get("rel") or r.get("path") or r.get("file"))[:88])

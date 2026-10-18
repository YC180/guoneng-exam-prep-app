import json, os
p = r"D:\app project\work\ocr\manifest.json"
if os.path.exists(p):
    m = json.load(open(p, encoding="utf-8"))
    recs = m if isinstance(m, list) else (m.get("files") or m.get("records") or [])
    from collections import Counter
    c = Counter((r.get("status") or "?") for r in recs)
    print(f"  清单条目 {len(recs)}；状态 {dict(c)}")
    pending = [r.get("rel") or r.get("source") or r.get("file") for r in recs
               if (r.get("status") or "") not in ("done", "ok", "skipped")]
    print(f"  未完成 {len(pending)} 个：")
    for x in pending[:14]:
        print("    " + str(x)[:88])

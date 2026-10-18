import json, os
d = json.load(open("bank/read_coverage.json", encoding="utf-8"))
rows = d if isinstance(d, list) else d.get("files", [])
n = 0
for r in rows:
    lvl = r.get("level") or r.get("tier") or r.get("verdict") or ""
    if "EMPTY" in str(lvl).upper() or "空" in str(lvl):
        n += 1
        print(f"  [{lvl}] chars={r.get('chars')}  {r.get('rel') or r.get('path')}")
print("EMPTY 共", n, "份")

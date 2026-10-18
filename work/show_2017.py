import os
stem = "2017年11月28日国电集团重组成立国家能源集团"
for d in ("text", "text2", "text3", "text4", "text5", "text6", "text7", "ocr", "ocr_ordered"):
    base = os.path.join("D:\\app project\\work", d)
    if not os.path.isdir(base): continue
    for dp, _dn, fs in os.walk(base):
        for fn in fs:
            if fn.endswith(".txt") and os.path.splitext(fn)[0] == stem:
                p = os.path.join(dp, fn)
                raw = open(p, encoding="utf-8", errors="replace").read()
                print(f"--- {os.path.relpath(p, '.')}  ({len(raw)} 字符)")
                print(raw.strip()[:600])
                print()

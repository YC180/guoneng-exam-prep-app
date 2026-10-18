import os, re
base = "ocr"
hits = []
for dp, _d, fs in os.walk(base):
    for fn in fs:
        if not fn.endswith(".txt"):
            continue
        p = os.path.join(dp, fn)
        t = open(p, encoding="utf-8", errors="replace").read()
        n_ansline = len(re.findall(r"答案为\s*[A-H]", t))
        n_qnum = len(re.findall(r"^\s*\d{1,3}[.、]", t, re.M))
        n_opt = len(re.findall(r"^\s*[A-D][.、]", t, re.M))
        if n_ansline >= 10:
            hits.append((n_ansline, n_qnum, n_opt, len(t), os.path.relpath(p, base)))
hits.sort(reverse=True)
print(f"含“答案为X。”≥10 处的 OCR 文件：{len(hits)} 个")
print(f"{'答案为':>6} {'题号':>5} {'选项':>5} {'字符':>8}  文件")
for a, q, o, c, rel in hits[:20]:
    print(f"{a:6d} {q:5d} {o:5d} {c:8d}  {rel[:70]}")

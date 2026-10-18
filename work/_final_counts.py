# -*- coding: utf-8 -*-
"""Definitive per-directory inventory numbers for the report."""
import json
import os
import sys

sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]

ROOTS = {
    "① 面试学习资料包": r"D:\DOWNLOADS\26国家能源集团通关资料\11、面试学习资料包",
    "② 专业知识": r"D:\DOWNLOADS\26国家能源集团通关资料\4、【专业知识】国家能源集团专业知识（近几年没考，可选看）",
}
MANIFEST = {
    "① 面试学习资料包": r"D:\app project\work\text4\面试\manifest.json",
    "② 专业知识": r"D:\app project\work\text4\专业知识\manifest.json",
}
OUTDIR = {
    "① 面试学习资料包": r"D:\app project\work\text4\面试",
    "② 专业知识": r"D:\app project\work\text4\专业知识",
}
MIN_CJK = 200

out = open(r"D:\app project\work\_final_counts.txt", "w", encoding="utf-8", newline="\n")


def body_cjk(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            t = fh.read()
    except OSError:
        return 0
    i = t.find("[[PAGE 1]]")
    b = t[i:] if i >= 0 else t
    return sum(1 for ch in b if "\u4e00" <= ch <= "\u9fff")


grand = {"files": 0, "bytes": 0, "readable": 0, "unreadable": 0}
for label, root in ROOTS.items():
    files = []
    for dp, _d, fns in os.walk(root):
        for n in fns:
            p = os.path.join(dp, n)
            files.append((os.path.relpath(p, root), os.path.getsize(p)))
    tot_b = sum(s for _r, s in files)
    out.write("### %s  文件数=%d  体积=%.1f MB\n" % (label, len(files), tot_b / 1048576))

    with open(MANIFEST[label], "r", encoding="utf-8") as fh:
        data = json.load(fh)
    # converted .doc/.ppt
    conv = []
    for dp, _d, fns in os.walk(OUTDIR[label]):
        for n in fns:
            if not n.lower().endswith(".txt"):
                continue
            p = os.path.join(dp, n)
            with open(p, "r", encoding="utf-8", errors="replace") as fh:
                head = fh.read(400)
            if "CONVERTED" in head:
                conv.append(os.path.relpath(p, OUTDIR[label]))

    rd = unr = 0
    per = {}
    unreadable = []
    for r in data:
        st = r.get("status")
        o = r.get("out")
        cjk = body_cjk(o) if o and os.path.exists(o) else 0
        bad = st in ("skipped-too-large", "error") or cjk < MIN_CJK
        top = r["rel"].split("\\")[0] if "\\" in r["rel"] else "(根目录)"
        a, b = per.get(top, (0, 0))
        per[top] = (a + (0 if bad else 1), b + (1 if bad else 0))
        if bad:
            unr += 1
            unreadable.append((r["rel"], r.get("size_mb", 0), st))
        else:
            rd += 1
    for r in sorted(per):
        out.write("   %-46s 可读 %2d  不可读 %2d\n" % (r, per[r][0], per[r][1]))
    out.write("   PDF/DOCX 可读=%d  不可读=%d  |  Word/PowerPoint COM 转换成功=%d\n" % (rd, unr, len(conv)))
    out.write("   本目录可读合计 = %d ；不可读合计 = %d\n" % (rd + len(conv), unr))
    grand["files"] += len(files)
    grand["bytes"] += tot_b
    grand["readable"] += rd + len(conv)
    grand["unreadable"] += unr
    out.write("   不可读明细:\n")
    for rel, mb, st in sorted(unreadable):
        out.write("      [%-18s] %7.2fMB  %s\n" % (st, mb, rel))
    out.write("\n")

out.write("### 总计  文件数=%d  体积=%.1f MB  可读=%d  不可读=%d\n" % (
    grand["files"], grand["bytes"] / 1048576, grand["readable"], grand["unreadable"]))
out.write("   注：不可读=%d 未含 .ppt（已成功转换，转换后计入可读）；若把「未处理」单列则为 0（本次 .ppt 已转换）。\n" % grand["unreadable"])
out.close()
print("written")

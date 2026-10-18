# -*- coding: utf-8 -*-
"""Compact inventory: per-subdirectory counts + manifest-derived readability + page counts."""
import json
import os
import sys

sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]

ROOTS = {
    "面试学习资料包": r"D:\DOWNLOADS\26国家能源集团通关资料\11、面试学习资料包",
    "专业知识": r"D:\DOWNLOADS\26国家能源集团通关资料\4、【专业知识】国家能源集团专业知识（近几年没考，可选看）",
}
MANIFEST = {
    "面试学习资料包": r"D:\app project\work\text4\面试\manifest.json",
    "专业知识": r"D:\app project\work\text4\专业知识\manifest.json",
}
OUT = {
    "面试学习资料包": r"D:\app project\work\text4\面试",
    "专业知识": r"D:\app project\work\text4\专业知识",
}

lines = []
for label, root in ROOTS.items():
    files = []
    for dp, _d, fns in os.walk(root):
        for n in fns:
            p = os.path.join(dp, n)
            files.append((os.path.relpath(p, root), os.path.getsize(p)))
    lines.append("=" * 78)
    lines.append("## %s" % label)
    lines.append("文件总数 %d，总体积 %.1f MB" % (len(files), sum(s for _r, s in files) / 1048576))
    ext = {}
    for r, s in files:
        e = os.path.splitext(r)[1].lower()
        a, b = ext.get(e, (0, 0))
        ext[e] = (a + 1, b + s)
    lines.append("扩展名: " + ", ".join("%s %d个/%.1fMB" % (e, ext[e][0], ext[e][1] / 1048576) for e in sorted(ext, key=lambda x: -ext[x][1])))
    sub = {}
    for r, s in files:
        if os.sep in r:
            top = r.split(os.sep)[0]
        else:
            top = "(根目录)"
        a, b = sub.get(top, (0, 0))
        sub[top] = (a + 1, b + s)
    lines.append("子目录:")
    for k in sorted(sub):
        lines.append("   %-58s %2d个 %8.1fMB" % (k, sub[k][0], sub[k][1] / 1048576))
    # manifest-based readability
    mpath = MANIFEST[label]
    data = []
    if os.path.exists(mpath):
        with open(mpath, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    lines.append("-- 可读性（PDF/DOCX/TXT 由提取脚本判定；.doc 由 Word COM 转换）--")
    for r in sorted(data, key=lambda x: x["rel"]):
        lines.append("   [%-17s] %7.2fMB pg=%-4s ch=%-8d %s" % (
            r.get("status"), r.get("size_mb", 0), r.get("pages", "-"), r.get("chars", 0), r["rel"]))
    # converted docs
    conv = []
    for dp, _d, fns in os.walk(OUT[label]):
        for n in fns:
            if n.lower().endswith(".txt"):
                p = os.path.join(dp, n)
                with open(p, "r", encoding="utf-8", errors="replace") as fh:
                    head = fh.read(400)
                if "CONVERTED" in head:
                    conv.append((os.path.relpath(p, OUT[label]), os.path.getsize(p)))
    lines.append("-- Word COM 转换的 .doc -> .txt : %d 个 --" % len(conv))
    for r, s in sorted(conv):
        lines.append("   %8dB  %s" % (s, r))

with open(r"D:\app project\work\_inv2.txt", "w", encoding="utf-8", newline="\n") as fh:
    fh.write("\n".join(lines) + "\n")
print("wrote %d lines" % len(lines))

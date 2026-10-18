# -*- coding: utf-8 -*-
"""Inventory of the two source directories plus merge with extraction manifests."""
import json
import os
import sys

sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]

ROOTS = {
    "面试": r"D:\DOWNLOADS\26国家能源集团通关资料\11、面试学习资料包",
    "专业知识": r"D:\DOWNLOADS\26国家能源集团通关资料\4、【专业知识】国家能源集团专业知识（近几年没考，可选看）",
}
MANIFEST = {
    "面试": r"D:\app project\work\text4\面试\manifest.json",
    "专业知识": r"D:\app project\work\text4\专业知识\manifest.json",
}
DOC_TXT = {
    "面试": r"D:\app project\work\text4\面试",
    "专业知识": r"D:\app project\work\text4\专业知识",
}

for label, root in ROOTS.items():
    print("=" * 78)
    print("### %s   root=%s" % (label, root))
    files = []
    for dp, _d, fns in os.walk(root):
        for n in fns:
            p = os.path.join(dp, n)
            files.append((os.path.relpath(p, root), os.path.getsize(p)))
    print("总文件数: %d   总体积: %.1f MB" % (len(files), sum(s for _r, s in files) / 1048576))
    ext = {}
    for r, s in files:
        e = os.path.splitext(r)[1].lower()
        a, b = ext.get(e, (0, 0))
        ext[e] = (a + 1, b + s)
    print("按扩展名:")
    for e in sorted(ext, key=lambda x: -ext[x][1]):
        print("   %-7s %3d 个  %9.1f MB" % (e, ext[e][0], ext[e][1] / 1048576))
    print("按子目录:")
    sub = {}
    for r, s in files:
        top = r.split(os.sep)[0]
        if os.sep not in r:
            top = "(根目录文件)"
        a, b = sub.get(top, (0, 0))
        sub[top] = (a + 1, b + s)
    for k in sorted(sub):
        print("   %-60s %3d 个  %9.1f MB" % (k[:58], sub[k][0], sub[k][1] / 1048576))
    print("全部文件清单:")
    for r, s in sorted(files):
        print("   %9.2fMB  %s" % (s / 1048576, r))

# doc conversions
print("=" * 78)
print("### .doc 转换结果")
for label, out in DOC_TXT.items():
    txts = []
    for dp, _d, fns in os.walk(out):
        for n in fns:
            if n.lower().endswith(".txt"):
                p = os.path.join(dp, n)
                with open(p, "r", encoding="utf-8", errors="replace") as fh:
                    head = fh.read(400)
                if "CONVERTED" in head:
                    txts.append((os.path.relpath(p, out), os.path.getsize(p)))
    print("%s: Word COM 转换 %d 个" % (label, len(txts)))
    for r, s in sorted(txts):
        print("   %8d B  %s" % (s, r))

# manifest merge
print("=" * 78)
print("### 提取清单（合并 .doc 转换）")
for label in ROOTS:
    with open(MANIFEST[label], "r", encoding="utf-8") as fh:
        data = json.load(fh)
    print("--- %s: %d 条 ---" % (label, len(data)))
    for r in sorted(data, key=lambda x: x["rel"]):
        print("   [%-18s] %7.2fMB %8dc  %s" % (r.get("status"), r.get("size_mb", 0), r.get("chars", 0), r["rel"]))

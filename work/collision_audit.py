#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""同名不同扩展名（X.pdf / X.docx / X.doc）碰撞审计。

extract.py 用 `os.path.splitext(rel)[0] + ".txt"` 命名输出，
因此同一目录下同名的 .pdf 与 .docx/.doc 会写到**同一个文件**，后者覆盖前者，
造成内容静默丢失。本脚本列出所有碰撞组，供补救提取。
"""
import json
import os
import sys
from collections import defaultdict

WORK = os.path.dirname(os.path.abspath(__file__))
ROOT = r"D:\DOWNLOADS\26国家能源集团通关资料"
OUT = os.path.join(WORK, "bank", "collision_audit.json")
TYPES = {".pdf", ".doc", ".docx", ".ppt", ".pptx", ".txt", ".md", ".xls", ".xlsx"}


def main():
    groups = defaultdict(list)
    for dp, _dn, fns in os.walk(ROOT):
        for fn in fns:
            stem, ext = os.path.splitext(fn)
            if ext.lower() in TYPES:
                groups[(dp, stem)].append(fn)

    coll = {k: v for k, v in groups.items() if len(v) > 1}
    print(f"同名不同扩展名碰撞组：{len(coll)} 组")
    lost_bytes = 0
    recs = []
    for (dp, stem), fns in sorted(coll.items(), key=lambda x: x[0][0]):
        rel_dir = os.path.relpath(dp, ROOT)
        items = []
        for fn in sorted(fns):
            p = os.path.join(dp, fn)
            items.append({"file": fn, "size_mb": round(os.path.getsize(p) / 1048576, 2)})
        print(f"\n  [{rel_dir}]  {stem}")
        for it in items:
            print(f"      {it['size_mb']:8.2f} MB  {it['file']}")
        recs.append({"dir": rel_dir, "stem": stem, "files": items})

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(recs, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n写出 {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

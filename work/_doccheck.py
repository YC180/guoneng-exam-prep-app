# -*- coding: utf-8 -*-
"""List .doc sources vs converted .txt, tagging which have a CONVERTED header."""
import os
import sys

sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]

root = r"D:\DOWNLOADS\26国家能源集团通关资料\11、面试学习资料包"
out = r"D:\app project\work\text4\面试"

docs = []
for dp, _d, fns in os.walk(root):
    for n in fns:
        if n.lower().endswith(".doc"):
            docs.append(os.path.relpath(os.path.join(dp, n), root))

print("%-5s %-9s %s" % ("state", "bytes", "file"))
for rel in sorted(docs):
    dest = os.path.join(out, os.path.splitext(rel)[0] + ".txt")
    if not os.path.exists(dest):
        print("%-5s %-9s %s" % ("MISS", "-", rel))
        continue
    with open(dest, "r", encoding="utf-8", errors="replace") as fh:
        head = fh.read(500)
    mark = "CONV" if "CONVERTED" in head else "????"
    print("%-5s %-9d %s" % (mark, os.path.getsize(dest), rel))

# -*- coding: utf-8 -*-
"""Audit extracted .txt files for NUL bytes / control-char defects that make them
unreadable by text tools, and report true usable character counts."""
import os
import sys

sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]

roots = [
    (r"D:\app project\work\text4\面试", "面试"),
    (r"D:\app project\work\text4\专业知识", "专业知识"),
]
for root, label in roots:
    rows = []
    for dp, _d, fns in os.walk(root):
        for n in sorted(fns):
            if not n.lower().endswith(".txt"):
                continue
            p = os.path.join(dp, n)
            with open(p, "rb") as fh:
                raw = fh.read()
            nul = raw.count(b"\x00")
            # count CJK chars
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                text = raw.decode("gb18030", "replace")
            cjk = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
            body = text.split("\n\n", 1)[-1] if "SOURCE:" in text else text
            bcjk = sum(1 for ch in body if "\u4e00" <= ch <= "\u9fff")
            rows.append((os.path.relpath(p, root), nul, len(text), cjk, bcjk))
    print("=" * 78)
    print("## %s  files=%d" % (label, len(rows)))
    bad = [r for r in rows if r[1] > 0]
    print("-- 含 NUL 字节（%d 个）--" % len(bad))
    for r in sorted(bad, key=lambda x: -x[1]):
        print("   nul=%-6d chars=%-8d cjk=%-7d %s" % (r[1], r[2], r[3], r[0]))
    print("-- 正文中文字符数最少（可能为扫描件/图片型）--")
    for r in sorted(rows, key=lambda x: x[4])[:25]:
        print("   body_cjk=%-7d nul=%-4d %s" % (r[4], r[1], r[0]))

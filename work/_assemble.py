# -*- coding: utf-8 -*-
"""Assemble the final report: existing head + the 6 subagent sections + closing sections."""
import io
import os
import sys

sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]

REPORT = r"D:\app project\work\reports\面试与专业知识归纳.md"
PARTS = r"D:\app project\work\reports\parts"

HEAD_END_MARK = "## 2. 面试备考要点归纳"

with open(REPORT, "r", encoding="utf-8") as fh:
    head = fh.read()
idx = head.find(HEAD_END_MARK)
assert idx > 0, "head marker not found"
head = head[:idx]

ORDER = [
    ("A_面试形式与测评要素.md", None),
    ("B_题型思路与答题模板.md", None),
    ("C_自我介绍着装与素材.md", None),
    ("D_专业知识_电气与热能.md", None),
    ("E_专业知识_计算机与通信.md", None),
    ("F_专业知识_财会金融管理.md", None),
]

chunks = [head]
for name, _ in ORDER:
    p = os.path.join(PARTS, name)
    with open(p, "r", encoding="utf-8") as fh:
        body = fh.read().strip()
    chunks.append(body)

# Normalise part headings to report numbering
body = "\n\n---\n\n".join(chunks)

out = body + "\n"
with open(REPORT, "w", encoding="utf-8", newline="\n") as fh:
    fh.write(out)
print("assembled: %d chars, %d lines" % (len(out), out.count("\n") + 1))

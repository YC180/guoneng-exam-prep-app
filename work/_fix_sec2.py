# -*- coding: utf-8 -*-
"""Fix remaining level-6 headings in sections 1-2."""
import os
import re
import sys

sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]

REPORT = r"D:\app project\work\reports\面试与专业知识归纳.md"
with open(REPORT, "r", encoding="utf-8") as fh:
    lines = fh.read().split("\n")

for i, l in enumerate(lines):
    if l == "###### 2.3.6 来源与缺口":
        # find enclosing ### section
        sec = None
        for k in range(i, -1, -1):
            m = re.match(r"^### (2\.\d) ", lines[k])
            if m:
                sec = m.group(1)
                break
        if sec == "2.5":
            lines[i] = "#### 2.5.5 来源与缺口"
        elif sec == "2.4":
            lines[i] = "#### 2.4.8 来源与缺口"
        else:
            lines[i] = "#### %s.7 来源与缺口" % (sec or "2.3")
    elif l.startswith("###### 2.4.7."):
        lines[i] = "##### " + l[7:]
    elif l == "###### 1. 实际读取的文件（共 11 个）":
        lines[i] = "##### 2.5.5.1 实际读取的文件（共 11 个）"
    elif l == "###### 2. 缺口与说明":
        lines[i] = "##### 2.5.5.2 缺口与说明"

text = "\n".join(lines)
text = re.sub(r"\n{4,}", "\n\n\n", text)
with open(REPORT, "w", encoding="utf-8", newline="\n") as fh:
    fh.write(text)

from collections import Counter
c = Counter(re.sub(r"^#+\s*", "", l) for l in text.split("\n") if re.match(r"^#{1,6} ", l))
dups = [(a, b) for a, b in c.items() if b > 1]
print("lines = %d ; duplicate headings = %d" % (text.count("\n") + 1, len(dups)))
for a, b in dups:
    print("   x%d %s" % (b, a))

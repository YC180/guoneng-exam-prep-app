# -*- coding: utf-8 -*-
"""Repair section 2 heading levels and numbering."""
import os
import re
import sys

sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]

REPORT = r"D:\app project\work\reports\面试与专业知识归纳.md"
with open(REPORT, "r", encoding="utf-8") as fh:
    lines = fh.read().split("\n")

lines = [l.replace("@@KEEP@@", "") for l in lines]

for i, l in enumerate(lines):
    if l.startswith("#### 2.4 自我介绍与着装要点"):
        lines[i] = "### 2.4 自我介绍与着装要点"
    elif l.startswith("#### 2.5 可背诵素材（金句／万能表达）"):
        lines[i] = "### 2.5 可背诵素材（金句／万能表达）"
    elif l == "#### 2.4.0 自我介绍":
        lines[i] = "#### 2.4.1 自我介绍"
    elif l.startswith("#### 2.4.7 面试着装"):
        lines[i] = "#### 2.4.2 面试着装"
    elif l.startswith("##### 2.4.7.1 "):
        lines[i] = "##### 2.4.2.1 " + l[len("##### 2.4.7.1 "):]
    elif l.startswith("##### 2.4.7.2 "):
        lines[i] = "##### 2.4.2.2 " + l[len("##### 2.4.7.2 "):]
    elif l.startswith("##### 2.4.7.3 "):
        lines[i] = "##### 2.4.2.3 " + l[len("##### 2.4.7.3 "):]

# two "2.3.7 来源与缺口": one belongs to 2.3, one to 2.5
seen = 0
for i, l in enumerate(lines):
    if l == "#### 2.3.7 来源与缺口":
        seen += 1
        lines[i] = "#### 2.3.6 来源与缺口" if seen == 1 else "#### 2.5.6 来源与缺口"

text = "\n".join(lines)
text = text.replace("（§2.4.7）", "（§2.4.2）").replace("§2.4.7 的原文条目", "§2.4.2 的原文条目")
text = re.sub(r"\n{4,}", "\n\n\n", text)
with open(REPORT, "w", encoding="utf-8", newline="\n") as fh:
    fh.write(text)

from collections import Counter
c = Counter(re.sub(r"^#+\s*", "", l) for l in text.split("\n") if re.match(r"^#{1,6} ", l))
dups = [(a, b) for a, b in c.items() if b > 1]
print("lines = %d ; duplicate headings = %d" % (text.count("\n") + 1, len(dups)))
for a, b in dups:
    print("   x%d %s" % (b, a))

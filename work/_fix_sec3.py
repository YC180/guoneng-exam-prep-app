# -*- coding: utf-8 -*-
"""Normalise the section-3 heading hierarchy:
### 3.N <方向>
  #### 3.N.a 代表资料 / 主要考点领域 / 题型 ...
    ##### 3.N.a.b ...
"""
import os
import re
import sys

sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]

REPORT = r"D:\app project\work\reports\面试与专业知识归纳.md"
with open(REPORT, "r", encoding="utf-8") as fh:
    lines = fh.read().split("\n")

start = next(i for i, l in enumerate(lines) if l.startswith("## 3. "))
end = next(i for i, l in enumerate(lines) if l.startswith("## 4. "))

cur = None          # current 3.N
sub = {}            # per-3.N counter for the #### level
out = []
for i in range(len(lines)):
    l = lines[i]
    if i < start or i >= end:
        out.append(l)
        continue

    m = re.match(r"^### (3\.\d) ", l)
    if m:
        cur = m.group(1)
        sub[cur] = 0
        out.append(l)
        continue

    # a level-4 sub-topic that is already numbered 3.N.x  -> keep as #####
    if re.match(r"^#### 3\.\d\.\d", l):
        out.append("##### " + l[5:])
        continue

    # unnumbered/loose headings that belong to the ### level of the section
    plain = re.sub(r"^#+\s*", "", l)
    if plain.startswith(("代表资料", "主要考点领域", "题型", "可读内容", "不可读清单",
                         "来源", "缺口", "读取与再现性说明", "读取方式与缺口",
                         "可直接引用的原文要点")):
        if cur:
            sub[cur] += 1
            sec = "%s.%d" % (cur, sub[cur])
            out.append("#### %s %s" % (sec, plain))
        else:
            out.append("#### " + plain)
        continue

    # leftover "###### N.N.N 来源与缺口" from a previous pass
    m = re.match(r"^#+\s*(\d+\.\d+\.\d+ 来源与缺口)$", l)
    if m and cur:
        sub[cur] += 1
        out.append("#### %s.%d %s" % (cur, sub[cur], m.group(1).split(" ", 1)[1]))
        continue

    out.append(l)

# leftover bare-level-6 headings inside section 3 -> promote to #####
for i in range(start, end):
    l = out[i]
    if l.startswith("###### ") and not re.match(r"^###### \d", l):
        out[i] = "##### " + l[7:]

text = "\n".join(out)
text = re.sub(r"\n{4,}", "\n\n\n", text)
with open(REPORT, "w", encoding="utf-8", newline="\n") as fh:
    fh.write(text)
print("normalised; lines = %d" % (text.count("\n") + 1))

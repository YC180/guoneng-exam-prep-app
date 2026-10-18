# -*- coding: utf-8 -*-
"""Measure the total line cost of '来源/缺口' blocks and the direct-quote blocks."""
import os
import re
import sys

sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]
_LOG = open(r"D:\app project\work\_sizes2.txt", "w", encoding="utf-8", newline="\n")
sys.stdout = _LOG

REPORT = r"D:\app project\work\reports\面试与专业知识归纳.md"
with open(REPORT, "r", encoding="utf-8") as fh:
    lines = fh.read().split("\n")

# 来源/缺口 家族：任何含「来源」「缺口」的 #### / ##### 标题
tot = 0
blocks = []
i = 0
while i < len(lines):
    l = lines[i]
    if re.match(r"^#{4,5} ", l) and ("来源" in l or "缺口" in l or "读取" in l or "再现性" in l):
        lvl = len(l) - len(l.lstrip("#"))
        j = i + 1
        while j < len(lines):
            m = re.match(r"^(#{1,6}) ", lines[j])
            if m and len(m.group(1)) <= lvl:
                break
            j += 1
        blocks.append((j - i, l))
        tot += j - i
        i = j
        continue
    i += 1
print("来源/缺口 家族合计 %d 行：" % tot)
for n, l in blocks:
    print("   %5d  %s" % (n, l))

# 可直接引用的原文要点
tot2 = 0
blocks2 = []
i = 0
while i < len(lines):
    l = lines[i]
    if re.match(r"^#{3,5} ", l) and "可直接引用的原文要点" in l:
        lvl = len(l) - len(l.lstrip("#"))
        j = i + 1
        while j < len(lines):
            m = re.match(r"^(#{1,6}) ", lines[j])
            if m and len(m.group(1)) <= lvl:
                break
            j += 1
        blocks2.append((j - i, l))
        tot2 += j - i
        i = j
        continue
    i += 1
print()
print("可直接引用的原文要点 合计 %d 行：" % tot2)
for n, l in blocks2:
    print("   %5d  %s" % (n, l))
_LOG.close()
print("ok", file=sys.stderr)

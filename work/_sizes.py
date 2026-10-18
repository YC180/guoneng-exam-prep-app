# -*- coding: utf-8 -*-
"""Measure line cost of each section and of the repeated '来源/缺口' blocks."""
import os
import re
import sys

sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]
_LOG = open(r"D:\app project\work\_sizes.txt", "w", encoding="utf-8", newline="\n")
sys.stdout = _LOG

REPORT = r"D:\app project\work\reports\面试与专业知识归纳.md"
with open(REPORT, "r", encoding="utf-8") as fh:
    lines = fh.read().split("\n")

heads = [(i, l) for i, l in enumerate(lines) if re.match(r"^#{2,3} ", l)]
for n, (i, l) in enumerate(heads):
    j = heads[n + 1][0] if n + 1 < len(heads) else len(lines)
    print("%6d lines  %s" % (j - i, l))

print()
print("-- lines spent in '来源'/'缺口' sub-blocks inside section 3 --")
tot = 0
cur = None
for i, l in enumerate(lines):
    if l.startswith("## 3. "):
        cur = True
    elif l.startswith("## 4. "):
        cur = False
    if cur and re.match(r"^#### 3\.\d\.10 ", l):
        # count until next heading of same-or-higher level
        j = i + 1
        while j < len(lines) and not re.match(r"^#{1,4} ", lines[j]):
            j += 1
        print("   %5d lines  %s" % (j - i, l))
        tot += j - i
print("   total: %d lines" % tot)

print()
print("-- lines spent in '可直接引用的原文要点' blocks --")
tot = 0
for i, l in enumerate(lines):
    if re.match(r"^#{3,5} 3\.\d\.9 可直接引用的原文要点", l) or re.match(r"^#{3,5} 2\.\d.*可直接引用的原文要点", l):
        j = i + 1
        while j < len(lines) and not re.match(r"^#{1,5} ", lines[j]):
            j += 1
        print("   %5d lines  %s" % (j - i, l))
        tot += j - i
print("   total: %d lines" % tot)
_LOG.close()
print("ok", file=sys.stderr)

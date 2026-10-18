# -*- coding: utf-8 -*-
"""Make section-3 numbering collision-free:
#### 3.N.<k> for the topic blocks;  ##### 3.N.<topic>.<j> for their children;
#### 3.N.9 可直接引用的原文要点 ; #### 3.N.10 来源与缺口
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

out = list(lines)
cur = None
k = 0            # #### counter within 3.N
topic = 0        # latest #### index that owns ##### children
j = 0            # ##### counter under topic

TOPIC_NAMES = ("代表资料", "主要考点领域", "题型", "可读内容", "不可读清单",
               "来源与缺口", "来源", "读取与再现性说明", "读取方式与缺口", "缺口")

for i in range(start, end):
    l = out[i]
    m = re.match(r"^### (3\.\d) ", l)
    if m:
        cur = m.group(1); k = 0; topic = 0; j = 0
        continue
    if not cur:
        continue

    m = re.match(r"^#### (?:3\.\d\.\d+ )?(.*)$", l)
    if m:
        plain = m.group(1)
        # "可直接引用的原文要点" always becomes .9
        if plain.startswith("可直接引用的原文要点"):
            out[i] = "#### %s.9 %s" % (cur, plain)
            topic = 9; j = 0
            continue
        if plain.startswith(TOPIC_NAMES):
            if plain.startswith("来源与缺口") or plain.startswith("读取方式与缺口"):
                out[i] = "#### %s.10 %s" % (cur, plain)
                topic = 10; j = 0
                continue
            k += 1
            out[i] = "#### %s.%d %s" % (cur, k, plain)
            topic = k; j = 0
            continue
        # any other #### that was a topic block
        k += 1
        out[i] = "#### %s.%d %s" % (cur, k, plain)
        topic = k; j = 0
        continue

    m = re.match(r"^##### (?:3\.\d(?:\.\d+)* )?(.*)$", l)
    if m:
        plain = m.group(1)
        if topic:
            j += 1
            out[i] = "##### %s.%d.%d %s" % (cur, topic, j, plain)
        continue

text = "\n".join(out)
text = re.sub(r"\n{4,}", "\n\n\n", text)
with open(REPORT, "w", encoding="utf-8", newline="\n") as fh:
    fh.write(text)

# report collisions
from collections import Counter
c = Counter(re.sub(r"^#+\s*", "", l) for l in text.split("\n") if re.match(r"^#{1,6} ", l))
dups = [(a, b) for a, b in c.items() if b > 1]
print("lines = %d ; duplicate headings = %d" % (text.count("\n") + 1, len(dups)))
for a, b in dups:
    print("   x%d %s" % (b, a))

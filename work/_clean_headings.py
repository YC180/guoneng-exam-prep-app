# -*- coding: utf-8 -*-
"""Clean up assembly artifacts: remove duplicated part titles, demote stray
second-level headings inside the merged sections, drop orphan '来源与缺口' heads."""
import os
import re
import sys

sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]

REPORT = r"D:\app project\work\reports\面试与专业知识归纳.md"
with open(REPORT, "r", encoding="utf-8") as fh:
    text = fh.read()

# 1) duplicated H1 part titles left over from assembly
for junk in [
    "# 国家能源集团招聘面试：面试形式与测评要素\n",
    "# 国家能源集团招聘面试·题型思路与答题模板\n",
    "# C 自我介绍·着装·可背诵素材归纳\n",
    "# 国家能源集团招聘《专业知识（电气工程类、热能工程与动力类、中国电力与能源战略）》考点归纳\n",
    "# E 专业知识：计算机类与通信类考点领域归纳\n",
    "# F 专业知识（财会类 / 金融类 / 管理类）考点领域归纳\n",
]:
    text = text.replace(junk, "")

# 2) demote the numbered section-2/3 headings that stayed at "### N." 
text = re.sub(r"^### (\d+\.\d+\.\d+ )", r"##### \1", text, flags=re.M)
text = re.sub(r"^### (\d+\.\d+ )", r"#### \1", text, flags=re.M)
text = re.sub(r"^### ([1-9]\. )", r"##### \1", text, flags=re.M)

# 3) demote the stray "### 四、来源与缺口" / "### 三、可直接引用的原文要点" etc.
for a, b in [
    ("### 四、来源与缺口", "#### 来源与缺口"),
    ("### 五、来源与缺口", "#### 来源与缺口"),
    ("### 三、可直接引用的原文要点", "#### 可直接引用的原文要点"),
    ("### 四、可直接引用的原文要点（逐字照抄 + 出处）", "#### 可直接引用的原文要点"),
    ("### 四、可直接引用的原文要点", "#### 可直接引用的原文要点"),
    ("### 来源", "##### 来源"),
    ("### 缺口", "##### 缺口"),
]:
    text = text.replace(a, b)

# 4) collapse runs of blank lines
text = re.sub(r"\n{4,}", "\n\n\n", text)

with open(REPORT, "w", encoding="utf-8", newline="\n") as fh:
    fh.write(text)
print("cleaned; lines = %d" % (text.count("\n") + 1))

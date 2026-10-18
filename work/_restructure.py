# -*- coding: utf-8 -*-
"""Final restructure of the report:
- fix the inventory/reconciliation numbers in section 1
- renumber top-level headings into a single 2..6 scheme
- append sections 4 (优先级建议), 5 (缺失/不可提取清单), 6 (复习要点速查)
"""
import io
import os
import re
import sys

sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]

REPORT = r"D:\app project\work\reports\面试与专业知识归纳.md"

with open(REPORT, "r", encoding="utf-8") as fh:
    text = fh.read()

# ---------------------------------------------------------------- 1) renumber
# map "## X、..." -> "### X、..." for the subagent sections, then insert ## 2/3 heads
def demote_after(text, start_marker, end_marker=None):
    i = text.index(start_marker)
    j = text.index(end_marker) if end_marker else len(text)
    seg = text[i:j]
    seg = re.sub(r"^## ", "### ", seg, flags=re.M)
    return text[:i] + seg + text[j:]


text = demote_after(text, "## 一、面试形式", "## 一、题型分类总览")
text = demote_after(text, "## 一、题型分类总览", "## 一、自我介绍")
text = demote_after(text, "## 一、自我介绍", "## 一、电气工程类")
text = demote_after(text, "## 一、电气工程类", "## 一、计算机类")
text = demote_after(text, "## 一、计算机类", "## 一、管理类")
text = demote_after(text, "## 一、管理类")

# insert the two big section heads
text = text.replace("### 一、面试形式", "## 2. 面试备考要点归纳\n\n### 2.1 面试形式", 1)
text = text.replace("### 一、题型分类总览", "### 2.3 常见题型分类、答题思路与模板要点\n\n#### 题型分类总览", 1)
text = text.replace("### 一、自我介绍", "### 2.5 自我介绍与着装要点\n\n#### 自我介绍", 1)
text = text.replace("### 一、电气工程类", "## 3. 专业知识板块归纳\n\n### 3.1 电气工程类", 1)
text = text.replace("### 一、计算机类", "### 3.4 计算机类", 1)
text = text.replace("### 一、管理类", "### 3.6 管理类", 1)

# renumber remaining second-level headings inside each part
renum = {
    "### 二、测评要素与考查依据": "### 2.2 测评要素与考查依据",
    "### 三、可直接引用的原文要点": "#### 2.2.1 可直接引用的原文要点",
    "### 四、来源与缺口": "#### 2.7 来源与缺口",
    "### 二、各题型答题思路（逐题型）": "#### 各题型答题思路（逐题型）",
    "### 三、答题模板与口诀": "#### 答题模板与口诀",
    "### 四、现象认知／职业认知 素材与解析要点": "#### 现象认知／职业认知 素材与解析要点",
    "### 五、可直接引用的原文要点": "#### 可直接引用的原文要点",
    "### 六、来源与缺口": "#### 来源与缺口",
    "### 二、面试着装": "#### 面试着装",
    "### 三、可背诵素材": "### 2.6 可背诵素材（金句／万能表达）",
    "### 二、热能工程与动力类": "### 3.2 热能工程与动力类",
    "### 三、中国电力与能源战略 + 电厂基础知识": "### 3.3 中国电力与能源战略与电厂基础知识",
    "### 二、通信类": "### 3.5 通信类",
    "### 二、金融类": "### 3.7 金融类",
    "### 三、财会类": "### 3.8 财会类",
}
for a, b in renum.items():
    text = text.replace(a, b, 1)

with open(REPORT, "w", encoding="utf-8", newline="\n") as fh:
    fh.write(text)
print("renumbered; lines = %d" % (text.count("\n") + 1))

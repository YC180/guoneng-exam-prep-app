# -*- coding: utf-8 -*-
"""Final pass: eliminate remaining duplicate heading numbers across merged parts."""
import os
import re
import sys

sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]

REPORT = r"D:\app project\work\reports\面试与专业知识归纳.md"
with open(REPORT, "r", encoding="utf-8") as fh:
    text = fh.read()

t = text
# --- 2.3.3 答题模板与口诀 : demote the 3.x children to level 5 ---
for n, title in [
    ("3.1", "口诀（逐条照抄原文，术语不改）"),
    ("3.2", "万能模板句式（来源：`3、…\\【面试万能模板】.txt`，逐条照抄）"),
    ("3.3", "套话篇（`【面试万能模板】.txt`，选录原文）"),
    ("3.4", "答题步骤（思考时间、开篇、主体、结尾）的原文表述"),
    ("3.5", "社会现象固定开头/结尾套句（`5、面试思维导图常用\\社会现象.txt`，照抄）"),
    ("3.6", "人际关系「具体答题」模板（`5、…\\人际关系.txt`，照抄）"),
    ("3.7", "组织计划/事件处理/情景模拟的开头固定语（照抄）"),
]:
    t = t.replace("### %s %s" % (n, title), "##### %s %s" % (n, title))

# --- 2.3.2 各题型答题思路 children 2.1-2.9 -> 2.3.2.x ---
for n, title in [
    ("2.1", "综合分析—社会现象／现象认知类"),
    ("2.2", "综合分析—观点题（分析观点类）五小题型"),
    ("2.3", "哲理题／名言警句／寓言故事"),
    ("2.4", "人际关系题"),
    ("2.5", "应急应变／事件处理类"),
    ("2.6", "组织计划／组织管理类"),
    ("2.7", "情景模拟（情境模拟）"),
    ("2.8", "自我认知与岗位匹配／职业认知类"),
    ("2.9", "演讲题／串词编故事／排序／小材料题（原文提及，思路照录）"),
]:
    t = t.replace("#### %s %s" % (n, title), "##### 2.3.2.%s %s" % (n[2:], title))

# --- 2.4 自我介绍与着装 ---
t = t.replace("#### 自我介绍\n", "#### 2.4.0 自我介绍\n")
t = t.replace("#### 2.4.7 面试着装", "#### 2.4.7 面试着装")

# --- section 3.1 电气: 领域 N -> 3.1.N ---
t = re.sub(r"^#### 领域 (\d+)：", lambda m: "#### 3.1.%s " % m.group(1), t, flags=re.M)
# --- section 3.2 热动, 3.3 战略: 领域 N -> 3.2.N / 3.3.N ---
# they appear in document order after 3.2 / 3.3 headings, so patch by position
lines = t.split("\n")
cur = None
for i, ln in enumerate(lines):
    m = re.match(r"^### (3\.[123]) ", ln)
    if m:
        cur = m.group(1)
        continue
    m = re.match(r"^#### 3\.1\.(\d+) ", ln)
    if m and cur and cur != "3.1":
        lines[i] = ln.replace("#### 3.1.%s " % m.group(1), "#### %s.%s " % (cur, m.group(1)))
t = "\n".join(lines)

# --- 3.4 计算机: "#### 2.N X（来源文件：...）" -> 3.4.N ---
lines = t.split("\n")
for i, ln in enumerate(lines):
    m = re.match(r"^#### 2\.(\d) (C 语言|信息系统分析与设计|操作系统|数据库系统|数据结构|计算机网络)", ln)
    if m:
        lines[i] = ln.replace("#### 2.%s " % m.group(1), "#### 3.4.%s " % m.group(1))
t = "\n".join(lines)
# 3.4 不可读清单 4.x -> 3.4.7.x
t = t.replace("#### 4.1 计算机类扫描件（6 份，`work\\text4\\专业知识\\计算机类\\1.计算机讲义\\`）",
              "#### 3.4.7.1 计算机类扫描件（6 份，`work\\text4\\专业知识\\计算机类\\1.计算机讲义\\`）")
t = t.replace("#### 4.2 计算机类超限文件（1 份）", "#### 3.4.7.2 计算机类超限文件（1 份）")

# --- 3.5 通信: "### 3.1/3.2 通信类扫描件/超限" -> 3.5.x ---
t = t.replace("### 3.1 通信类扫描件（11 份）", "#### 3.5.1 通信类扫描件（11 份）")
t = t.replace("### 3.2 通信类超限文件（3 份，未生成 .txt）", "#### 3.5.2 通信类超限文件（3 份，未生成 .txt）")

# --- 3.6 管理 ---
t = re.sub(r"^#### （(\d)）(复习讲义|客观题|主观题) ", lambda m: "#### 3.6.%s %s " % (m.group(1), m.group(2)), t, flags=re.M)
lines = t.split("\n")
for i, ln in enumerate(lines):
    m = re.match(r"^#### 2\.(\d) (人力资源管理|企业战略管理|现代企业管理|管理学原理|行政管理)（来源：", ln)
    if m:
        lines[i] = ln.replace("#### 2.%s " % m.group(1), "#### 3.6.4.%s " % m.group(1))
t = "\n".join(lines)

# --- 3.7 金融 ---
lines = t.split("\n")
for i, ln in enumerate(lines):
    m = re.match(r"^#### 2\.(\d) (微观经济学|宏观经济学|中级计量经济学|金融学|金融经济学)（", ln)
    if m:
        lines[i] = ln.replace("#### 2.%s " % m.group(1), "#### 3.7.2.%s " % m.group(1))
t = "\n".join(lines)

# --- 3.8 财会: "#### （N）..." -> 3.8.N ---
t = re.sub(r"^#### （(\d)）(代表资料|可读内容|不可读清单)", lambda m: "#### 3.8.%s %s" % (m.group(1), m.group(2)), t, flags=re.M)

# --- duplicate "2.3.5 可直接引用的原文要点" inside sections 3.3/3.5/3.8 ---
lines = t.split("\n")
cur = None
for i, ln in enumerate(lines):
    m = re.match(r"^### (3\.\d) ", ln)
    if m:
        cur = m.group(1)
    if ln.strip() == "#### 2.3.5 可直接引用的原文要点" and cur:
        lines[i] = "#### %s.9 可直接引用的原文要点" % cur
t = "\n".join(lines)

# --- 4/5/6 sub-headings -> level 3 ---
t = re.sub(r"^#### (4\.\d|5\.\d|6\.\d) ", lambda m: "### %s " % m.group(1), t, flags=re.M)

# --- duplicate "#### 来源与缺口" inside 3.x: give explicit numbers ---
lines = t.split("\n")
count = {}
for i, ln in enumerate(lines):
    if ln.strip() == "#### 来源与缺口":
        # find enclosing 3.x
        for j in range(i, -1, -1):
            m = re.match(r"^### (3\.\d) ", lines[j])
            if m:
                sec = m.group(1)
                count[sec] = count.get(sec, 0) + 1
                lines[i] = "#### %s.10 来源与缺口" % sec
                break
t = "\n".join(lines)

t = re.sub(r"\n{4,}", "\n\n\n", t)
with open(REPORT, "w", encoding="utf-8", newline="\n") as fh:
    fh.write(t)
print("final renumber done; lines = %d" % (t.count("\n") + 1))

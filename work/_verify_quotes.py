# -*- coding: utf-8 -*-
"""Spot-check: verify that quoted key phrases in the report really exist in the
extracted source text. Reports any quote that cannot be found."""
import os
import re
import sys

sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]

SRC_ROOTS = [
    r"D:\app project\work\text4\面试",
    r"D:\app project\work\text4\专业知识",
]
# corpus: normalise whitespace
corpus = []
for root in SRC_ROOTS:
    for dp, _d, fns in os.walk(root):
        for n in fns:
            if n.lower().endswith(".txt"):
                with open(os.path.join(dp, n), "r", encoding="utf-8", errors="replace") as fh:
                    t = fh.read()
                corpus.append(re.sub(r"\s+", "", t))
CORPUS = "\n".join(corpus)
print("corpus chars: %d" % len(CORPUS))

QUOTES = [
    "半结构化面试（Semi—structured Interview,简称 SSI），是介于非结构化面试和结构化面试之间的一种形式",
    "除专业类问题外，各题型所占的比重约为 10%、60%、20%、10%",
    "行为是判断一个人的最终依据，过去的行为是未来业绩的最佳预测因素",
    "行动是整个 STAR 的关键",
    "行为事件访谈法（Behavioral Event Interview，BEI）",
    "结构化小组面试这一面试形式，起初只在海南国税中得以运用",
    "讨论过程中 HR 关注的人",
    "结构化面试考试中，常见的有五种题型，分别是综合分析、计划组织协调、人际关系、应变能力、求职动机",
    "帽子",
    "鞋子",
    "事前准备，全面开展",
    "应用本试题面试的时间控制在30-45分钟",
    "首先请报出自己的姓名和身份",
    "展示自己的亮点；激发考官继续提问的兴趣；紧密结合应聘岗位以及公司企业文化",
    "言必信，行必果",
    "君子一言，驷马难追",
    "请您先用1分钟内时间介绍一下自己",
    "你为什么要申请加入我们公司",
    "请用2-3分钟简单的描述一下您自己",
    "电力电子技术",
    "晶闸管",
    "基尔霍夫",
    "戴维南",
    "对称分量法",
    "距离保护",
    "标幺值",
    "传热学",
    "工程热力学",
    "汽轮机",
    "锅炉",
    "流体力学",
    "热力学第一定律",
    "卡诺循环",
    "朗肯循环",
    "C 语言简洁、紧凑，使用方便、灵活",
    "瀑布模型",
    "银行家算法",
    "三级模式",
    "哈夫曼树",
    "TCP",
    "五力",
    "SWOT",
    "CAPM",
    "IS-LM",
    "借贷记账法",
]

miss = []
hit = 0
for q in QUOTES:
    norm = re.sub(r"\s+", "", q)
    if norm in CORPUS:
        hit += 1
    else:
        miss.append(q)

print("verified %d / %d" % (hit, len(QUOTES)))
print("NOT FOUND (%d):" % len(miss))
for q in miss:
    print("   - %s" % q)

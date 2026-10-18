# -*- coding: utf-8 -*-
"""Re-verify quotes against a normalised corpus.

The PDF text layer doubles bold glyphs ("⼩小组" = 小 + 小组, "⾯面试" = 面 + 面试)
and uses CJK compatibility ideographs (U+2F00..U+2FDF radicals, U+F900..U+FAFF).
Normalise by deleting Kangxi radicals and collapsing doubled leading chars.
"""
import os
import re
import sys

sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]
_LOG = open(r"D:\app project\work\_verify2.txt", "w", encoding="utf-8", newline="\n")
sys.stdout = _LOG

SRC_ROOTS = [
    r"D:\app project\work\text4\面试",
    r"D:\app project\work\text4\专业知识",
]

KANGXI = re.compile(r"[\u2e80-\u2fdf\uf900-\ufaff]")


def norm(t):
    t = KANGXI.sub("", t)                     # drop Kangxi radicals / compat ideographs
    t = re.sub(r"\s+", "", t)
    # collapse "X X..." where a single char is repeated immediately (bold doubling)
    t = re.sub(r"([\u4e00-\u9fff])\1(?=[\u4e00-\u9fff])", r"\1", t)
    return t


corpus = []
for root in SRC_ROOTS:
    for dp, _d, fns in os.walk(root):
        for n in fns:
            if n.lower().endswith(".txt"):
                with open(os.path.join(dp, n), "r", encoding="utf-8", errors="replace") as fh:
                    corpus.append(norm(fh.read()))
CORPUS = "\n".join(corpus)
print("corpus chars: %d" % len(CORPUS))

QUOTES = [
    # 面试
    "半结构化面试（Semi—structured Interview,简称 SSI），是介于非结构化面试和结构化面试之间的一种形式",
    "除专业类问题外，各题型所占的比重约为 10%、60%、20%、10%",
    "行为是判断一个人的最终依据，过去的行为是未来业绩的最佳预测因素",
    "行动是整个 STAR 的关键",
    "行为事件访谈法",
    "起初只在海南国税中得以运用",
    "讨论过程中 HR 关注的人",
    "常见的有五种题型，分别是综合分析、计划组织协调、人际关系、应变能力、求职动机",
    "事前准备，全面开展",
    "应用本试题面试的时间控制在30-45分钟",
    "首先请报出自己的姓名和身份",
    "展示自己的亮点；激发考官继续提问的兴趣；紧密结合应聘岗位以及公司企业文化",
    "言必信，行必果",
    "请您先用1分钟内时间介绍一下自己",
    "请用2-3分钟简单的描述一下您自己",
    "结构化小组面试结合了结构化面试和无领导小组讨论的特点",
    # 电气
    "电力电子技术",
    "晶闸管",
    "对称分量法",
    "标幺值",
    "继电保护",
    "差动保护",
    "瓦斯保护",
    "卡诺图",
    "555 定时器",
    "PN 结",
    # 热动 / 战略
    "传热学",
    "工程热力学",
    "汽轮机",
    "锅炉",
    "流体力学",
    "热力学第一定律",
    "卡诺循环",
    "朗肯循环",
    "电厂",
    # 计算机 / 通信
    "瀑布模型",
    "银行家算法",
    "三级模式",
    "哈夫曼树",
    "数据流图",
    "耦合度",
    "内聚度",
    "SQL",
    # 管理 / 金融
    "SWOT",
    "CAPM",
    "IS-LM",
    "借贷记账法",
]

hit = []
miss = []
for q in QUOTES:
    if norm(q) in CORPUS:
        hit.append(q)
    else:
        miss.append(q)

print("verified %d / %d" % (len(hit), len(QUOTES)))
print("NOT FOUND (%d):" % len(miss))
for q in miss:
    print("   - %s" % q)

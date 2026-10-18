# -*- coding: utf-8 -*-
"""Count question markers in key interview text files to populate the inventory."""
import io
import os
import re
import sys

sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE = r"D:\app project\work\text4\面试"
TARGETS = [
    r"8、面试题3000（赠送；时间多可参考看）\面试大全1500题.txt",
    r"8、面试题3000（赠送；时间多可参考看）\结构化面试经典100题.txt",
    r"8、面试题3000（赠送；时间多可参考看）\20大面试模拟题汇总.txt",
    r"8、面试题3000（赠送；时间多可参考看）\人际沟通例题100 题.txt",
    r"9、结构化面试\【结构化、结构化小组】面试真经.txt",
    r"9、结构化面试\结构化面试各题型模板总结.txt",
    r"现象认知题目加解析.txt",
    r"职业认知题目加解析.txt",
    r"职业认知素材梳理汇总.txt",
    r"4、面试技巧+经验分享+总结+参考背诵\面试总结.txt",
]

# question-number patterns common in these banks
PATS = [
    ("题N、", re.compile(r"^\s*(?:第)?\s*\d{1,4}\s*[、．.]\s*(?=\S)")),
    ("问：", re.compile(r"问\s*[:：]")),
    ("答：", re.compile(r"答\s*[:：]")),
    ("【例题】", re.compile(r"【例\s*题】|例题\s*\d*")),
    ("问号结尾行", re.compile(r"[？?]\s*$")),
]

for rel in TARGETS:
    p = os.path.join(BASE, rel)
    if not os.path.exists(p):
        print("MISSING %s" % rel)
        continue
    with open(p, "r", encoding="utf-8", errors="replace") as fh:
        lines = fh.read().split("\n")
    print("=" * 74)
    print("%s   lines=%d  chars=%d" % (rel, len(lines), sum(len(x) for x in lines)))
    for name, rx in PATS:
        n = sum(1 for x in lines if rx.search(x))
        print("   %-12s %d" % (name, n))
    # page markers
    pages = sum(1 for x in lines if x.startswith("[[PAGE"))
    print("   %-12s %d" % ("PAGE标记", pages))
    # first few numbered-question lines as evidence
    shown = 0
    for x in lines:
        if PATS[0][1].search(x) and len(x.strip()) > 8:
            print("      e.g. %s" % x.strip()[:90])
            shown += 1
            if shown >= 3:
                break

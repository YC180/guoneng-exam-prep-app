#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""打印候选时政题库文件的结构样本，判断能否用 numbered 解析器接入。"""
import os
import sys

WORK = os.path.dirname(os.path.abspath(__file__))
T2 = os.path.join(WORK, "text2")
BASE = os.path.join(T2, r"【全国时政】全国时政热点（已更4月）\24-26年时政")

FILES = [
    (BASE, r"2024年时政热点+试题\24年12月\24年1月-24年12月时政要问及1950题及答案（24年12月更新完）.txt"),
    (BASE, r"2025年每月时政热点配套押题\8月押题\2025年8月时政试题173道.txt"),
    (BASE, r"2025年每月时政热点配套押题\3月押题\2025年3月时事政治模拟题(带答案).txt"),
    (BASE, r"2024年时政热点+试题\24年11月\2024年11月时事政治模拟题及答案（160题）.txt"),
]
EXTRA = [
    (os.path.join(WORK, "text"), "2012年国电集团招聘笔试试题及答案.txt"),
]


def show(base, rel, head=16, tail=10):
    p = os.path.join(base, rel)
    if not os.path.exists(p):
        print(f"缺失 {rel}")
        return
    lines = open(p, encoding="utf-8", errors="replace").read().split("\n")
    print(f"\n########## {os.path.basename(rel)}  （{len(lines)} 行）")
    for l in lines[:head]:
        print("  | " + l[:110])
    print("  ......")
    for l in lines[-tail:]:
        print("  | " + l[:110])


def main():
    for base, rel in FILES + EXTRA:
        show(base, rel)
    return 0


if __name__ == "__main__":
    sys.exit(main())

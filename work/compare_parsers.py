#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""对比 numbered 与 inline 两种解析器在时政题库文件上的表现。"""
import os
import sys
from collections import Counter

WORK = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, WORK)
import build_bank as B  # noqa: E402

T2 = os.path.join(WORK, "text2")
T2R = "【全国时政】全国时政热点（已更4月）"

FILES = [
    f"{T2R}\\24-26年时政\\2024年时政热点+试题\\24年12月\\24年1月-24年12月时政要问及1950题及答案（24年12月更新完）.txt",
    f"{T2R}\\24-26年时政\\2024年时政热点+试题\\24年11月\\2024年11月时事政治模拟题及答案（160题）.txt",
    f"{T2R}\\24-26年时政\\2025年每月时政热点配套押题\\1月押题\\2025年1月时事政治模拟题(带答案).txt",
    f"{T2R}\\24-26年时政\\2025年每月时政热点配套押题\\3月押题\\2025年3月时事政治模拟题(带答案).txt",
    f"{T2R}\\24-26年时政\\2025年每月时政热点配套押题\\5月押题\\2025年5月时事政治模拟题(带答案).txt",
    f"{T2R}\\24-26年时政\\2025年每月时政热点配套押题\\7月押题\\2025年7月时政183题.txt",
    f"{T2R}\\24-26年时政\\2025年每月时政热点配套押题\\8月押题\\2025年8月时政试题173道.txt",
    f"{T2R}\\24-26年时政\\2025年每月时政热点配套押题\\6月押题\\2025年6月时事政治模拟题及答案（带答案）.txt",
    f"{T2R}\\【重要会议】2025重要时政+文章考点\\2025年中央一号文件\\2025年中央一号文件（全文+划重点+58题）.txt",
    f"{T2R}\\【重要会议】2025重要时政+文章考点\\2026年\\试题21道  2026.2.27中央政治局会议.txt",
    f"{T2R}\\24-26年时政\\2026年时政+试题\\2026年4月时政试题165道.txt",
]


def run(rel, mode):
    p = os.path.join(T2, rel)
    if not os.path.exists(p):
        return None
    raw = open(p, encoding="utf-8", errors="replace").read()
    lines = B.expand_inline_options(B.clean_lines(raw))
    return B.parse_inline_answer(lines, {}) if mode == "inline" else B.parse_numbered(lines, {})


def main():
    print(f"{'文件':52s} {'numbered':>18s} {'inline':>18s}")
    tot = Counter()
    for rel in FILES:
        a = run(rel, "numbered")
        b = run(rel, "inline")
        def fmt(qs):
            if qs is None:
                return "—"
            c = Counter(q["answerStatus"] for q in qs)
            return f"{len(qs):5d}题/ok={c.get('verified',0):4d}"
        print(f"{os.path.basename(rel)[:52]:52s} {fmt(a):>18s} {fmt(b):>18s}")
        if b:
            c = Counter(q["answerStatus"] for q in b)
            tot["inline_total"] += len(b)
            tot["inline_ok"] += c.get("verified", 0)
            tot["inline_missing"] += c.get("missing", 0)
    print(f"\ninline 合计 {tot['inline_total']} 题，ok={tot['inline_ok']}，missing={tot['inline_missing']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

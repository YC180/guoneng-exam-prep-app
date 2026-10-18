#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""查看 inline 解析后仍失败/缺答案的具体题目，判断原因。"""
import os
import sys
from collections import Counter

WORK = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, WORK)
import build_bank as B  # noqa: E402

T2 = os.path.join(WORK, "text2")
T2R = "【全国时政】全国时政热点（已更4月）"

TARGETS = [
    (f"{T2R}\\24-26年时政\\2024年时政热点+试题\\24年11月\\2024年11月时事政治模拟题及答案（160题）.txt", "2024年11月"),
    (f"{T2R}\\24-26年时政\\2025年每月时政热点配套押题\\6月押题\\2025年6月时事政治模拟题及答案（带答案）.txt", "2025年6月"),
]


def main():
    for rel, tag in TARGETS:
        p = os.path.join(T2, rel)
        raw = open(p, encoding="utf-8", errors="replace").read()
        lines = B.expand_inline_options(B.clean_lines(raw))
        qs = B.parse_inline_answer(lines, {})
        c = Counter(q["answerStatus"] for q in qs)
        print(f"\n########## {tag}  {len(qs)} 题  {dict(c)}")
        bad = [q for q in qs if q["answerStatus"] != "verified"]
        print(f"  非 verified 共 {len(bad)} 题，示例前 5：")
        for q in bad[:5]:
            print(f"    [{q['answerStatus']}] ans={'/'.join(q['answer'])} keys={[o['key'] for o in q['options']]}")
            print(f"      stem: {q['stem'][:96]}")
            print(f"      opts: {[o['key'] + '.' + o['text'][:16] for o in q['options']]}")
            print(f"      expl: {(q['explanation'] or '')[:70]!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

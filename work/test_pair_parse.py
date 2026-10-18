#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""验证：一号文件模拟试题（题目+答案解析 pair）与补救 OCR 来源能否正确解析。"""
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_bank as B  # noqa: E402


def main():
    print("=== pair：2025年中央一号文件·模拟试题")
    for qf, af, cat, ch, tags in B.SOURCES_PAIR:
        p = os.path.join(B.TEXT2, qf)
        a = os.path.join(B.TEXT2, af)
        print(f"  题目存在 {os.path.exists(p)}，答案存在 {os.path.exists(a)}")
        if not (os.path.exists(p) and os.path.exists(a)):
            continue
        qs = B.parse_pair(p, a, {})
        tc = Counter(q["answerStatus"] for q in qs)
        print(f"  解析 {len(qs)} 题  {dict(tc)}")
        for q in qs[:3]:
            print(f"    题干: {q['stem'][:64]}")
            print(f"    选项: {[o['key'] + '.' + o['text'][:10] for o in q['options']]}")
            print(f"    答案: {q['answer']}  解析: {q['explanation'][:52]!r}")
    print()
    print("=== 补救 OCR 来源发现情况")
    found = B.discover_ocr_sources()
    for rel, cat, ch, tags in found:
        flag = "（含补救）" if "重要讲话" in rel or "政治局" in rel else ""
        print(f"  [{cat}] {ch}  {os.path.basename(rel)[:56]} {flag}")
    print(f"  合计 {len(found)} 个 OCR 来源")
    return 0


if __name__ == "__main__":
    sys.exit(main())

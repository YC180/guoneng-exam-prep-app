#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检测时政题库文件是否为“双栏 PDF”导致的错行/错序文本。

判据：同一行里出现多个选项字母时，若字母顺序并非 A→B→C→D，说明两栏内容
被交错合并，选项正文不可靠 —— 这类文件应改走 OCR，而不是直接用文本层。
"""
import os
import re
import sys

WORK = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, WORK)
import build_bank as B  # noqa: E402

T2 = os.path.join(WORK, "text2")
T2R = "【全国时政】全国时政热点（已更4月）"
OPT_LETTERS = re.compile(r"([A-D])\s*[．.、]")


def ratio(path):
    raw = open(path, encoding="utf-8", errors="replace").read()
    lines = B.clean_lines(raw)
    total = bad = 0
    for t, _p in lines:
        letters = OPT_LETTERS.findall(t)
        if len(letters) >= 2:
            total += 1
            if letters != sorted(letters):
                bad += 1
    return bad, total, (bad / total if total else 0.0)


def main():
    from build_bank import SOURCES_T2
    rows = []
    for rel, ch in SOURCES_T2:
        p = os.path.join(T2, rel)
        if not os.path.exists(p):
            continue
        bad, total, r = ratio(p)
        rows.append((r, bad, total, os.path.basename(rel), rel))
    rows.sort(reverse=True)
    print(f"{'错序率':>7s} {'错序行':>6s} {'多选项行':>7s}  文件")
    for r, bad, total, name, rel in rows:
        flag = "  ← 需 OCR" if r > 0.20 else ""
        print(f"{r*100:6.1f}% {bad:6d} {total:7d}  {name[:52]}{flag}")
    print(f"\n共 {len(rows)} 个文件")
    return 0


if __name__ == "__main__":
    sys.exit(main())

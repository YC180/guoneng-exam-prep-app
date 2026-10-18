#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""汇总题库统计，供 README 与归纳文档引用。"""
import json
import os
import sys
from collections import Counter

WORK = os.path.dirname(os.path.abspath(__file__))
BANK = os.path.join(WORK, "bank", "questions.json")


def main():
    qs = json.load(open(BANK, encoding="utf-8"))["questions"]
    n = len(qs)
    print(f"总题数 {n}")
    print("状态:", dict(Counter(q["answerStatus"] for q in qs)))
    print("题型:", dict(Counter(q["type"] for q in qs)))
    print("类别:", dict(Counter(q.get("category") for q in qs)))
    ocr = [q for q in qs if "OCR" in (q.get("tags") or [])]
    print(f"OCR 题：{len(ocr)}（占 {len(ocr)/n*100:.1f}%）")
    print(f"无解析：{sum(1 for q in qs if not (q.get('explanation') or '').strip())}")
    print(f"有来源文件：{sum(1 for q in qs if q.get('sourceFile'))}")
    print(f"有来源页码：{sum(1 for q in qs if q.get('sourcePage'))}")
    print(f"有标签：{sum(1 for q in qs if q.get('tags'))}")
    print("\nOCR 来源明细：")
    for s, c in Counter(q["sourceFile"] for q in ocr).most_common():
        print(f"  {c:5d}  {os.path.basename(s)[:64]}")
    print("\n题量最多的来源（前 12）：")
    for s, c in Counter(q["sourceFile"] for q in qs).most_common(12):
        print(f"  {c:5d}  {os.path.basename(s)[:64]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

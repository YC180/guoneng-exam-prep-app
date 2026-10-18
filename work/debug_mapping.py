#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""调试覆盖度审计的 SOURCE 映射为何漏掉若干文件。"""
import os
import re
import sys

WORK = os.path.dirname(os.path.abspath(__file__))
ROOT = r"D:\DOWNLOADS\26国家能源集团通关资料"
SRC_RE = re.compile(r"^#\s*SOURCE:\s*(.+?)\s*$", re.MULTILINE)

SAMPLES = [
    r"text2\【全国时政】全国时政热点（已更4月）\【重要会议】2025重要时政+文章考点\2025年中央一号文件\2025年中央一号文件-资料包\【模拟试题】2025年中央一号文件-答案解析.txt",
    r"text\1、2025国家能源集团招聘考试知识点讲义和企业文化\国家能源集团企业文化试题.txt",
    r"text2\8、时政\【全国时政】全国时政热点（已更4月）\【重要会议】2025重要时政+文章考点\2025年中央一号文件\2025年中央一号文件（全文+划重点+58题）.txt",
]


def norm(p):
    return os.path.normcase(os.path.abspath(p)).rstrip("\\/")


def main():
    for rel in SAMPLES:
        fp = os.path.join(WORK, rel)
        if not os.path.exists(fp):
            print(f"缺失: {rel}")
            continue
        with open(fp, encoding="utf-8", errors="replace") as fh:
            head = fh.read(600)
        m = SRC_RE.search(head)
        first = head.split("\n", 1)[0]
        print(f"文件: {os.path.basename(fp)}")
        print(f"  首行 repr: {first[:120]!r}")
        print(f"  首字符码点: U+{ord(head[0]):04X}")
        if m:
            src = m.group(1)
            print(f"  解析到源: {src[:110]}")
            print(f"  规范化后 : {norm(src)[:110]}")
            print(f"  文件存在 : {os.path.exists(src)}")
        else:
            print("  ✗ 正则未匹配")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())

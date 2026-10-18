#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""诊断解析失败的时政题库文件的实际结构。"""
import os
import re
import sys
from collections import Counter

WORK = os.path.dirname(os.path.abspath(__file__))
T2 = os.path.join(WORK, "text2")
B = os.path.join(T2, "【全国时政】全国时政热点（已更4月）", "24-26年时政")

FILES = [
    (B, r"2024年时政热点+试题\24年01月\2024年1月政热点试题及答案(OCR).txt"),
    (B, r"2024年时政热点+试题\24年02月\2024年2时政热点试题及答案.txt"),
    (B, r"2024年时政热点+试题\24年11月\2024年11月时事政治模拟题及答案（160题）.txt"),
    (B, r"24年12月\24年1月-24年12月时政要问及1950题及答案（24年12月更新完）.txt"),
    (B, r"2025年每月时政热点配套押题\6月押题\2025年6月时事政治模拟题及答案（带答案）.txt"),
    (B, r"2025年每月时政热点配套押题\8月押题\2025年8月时政试题173道.txt"),
]

QNO = re.compile(r"^\s*(\d{1,4})\s*[．.、]\s*(\S.*)$", re.M)
ANS_KEY = re.compile(r"^\s*答\s*案\s*[:：]?\s*([A-Ha-h]{1,6}|正确|错误)", re.M)
ANS_REF = re.compile(r"^\s*参\s*考\s*答\s*案\s*[:：]\s*([A-Ha-h]{1,6})", re.M)
ANS_BR = re.compile(r"【\s*答\s*案\s*】\s*[:：]?\s*([A-Ha-h]{1,6})", re.M)
OPT_LINE = re.compile(r"^\s*[A-D]\s*[．.、]", re.M)
OPT_INLINE = re.compile(r"[A-D]\s*[．.、]\s*\S.*?[A-D]\s*[．.、]", re.M)
ANS_SECTION = re.compile(r"(参考答案|答案及解析|答案汇总|试题答案|答案)\s*$", re.M)


def show(base, rel, head=14):
    p = os.path.join(base, rel)
    if not os.path.exists(p):
        print(f"\n##### 缺失: {rel}")
        return
    t = open(p, encoding="utf-8", errors="replace").read()
    lines = t.split("\n")
    print(f"\n##### {os.path.basename(rel)}  {len(lines)} 行 / {len(t)} 字符")
    print(f"  题号行={len(QNO.findall(t))}  '答案X'={len(ANS_KEY.findall(t))}  "
          f"'参考答案：'={len(ANS_REF.findall(t))}  '【答案】'={len(ANS_BR.findall(t))}  "
          f"选项起行={len(OPT_LINE.findall(t))}  同行多选项={len(OPT_INLINE.findall(t))}")
    for l in lines[:head]:
        print("  | " + l[:108])
    # 找第一个答案标记附近
    for i, l in enumerate(lines):
        if ANS_KEY.match(l) or ANS_REF.match(l) or ANS_BR.match(l):
            print("  --- 首个答案标记附近 ---")
            for l2 in lines[max(0, i - 6):i + 3]:
                print("  ~ " + l2[:108])
            break


def main():
    for base, rel in FILES:
        show(base, rel)
    return 0


if __name__ == "__main__":
    sys.exit(main())

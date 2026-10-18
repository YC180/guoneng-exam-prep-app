#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""诊断 2014/2015/2022 真题 OCR 文本为何解析不出题目。"""
import os
import re
import sys

WORK = os.path.dirname(os.path.abspath(__file__))
OCR = os.path.join(WORK, "ocr", "6、【国家能源集团招聘】12-25年笔试真题")

Q = re.compile(r"^\s*(\d{1,3})\s*[．.、]\s*(\S.*)$", re.M)
OPT = re.compile(r"^\s*([A-D])\s*[．.、]\s*(.*)$", re.M)
ANS = re.compile(r"(【\s*答\s*案\s*】|参\s*考\s*答\s*案|答\s*[案家]\s*[:：]?)", re.M)
LONE = re.compile(r"^\s*[A-D]\s*$", re.M)


def main():
    for fn in sorted(os.listdir(OCR)) if os.path.isdir(OCR) else []:
        if not fn.endswith(".txt"):
            continue
        p = os.path.join(OCR, fn)
        t = open(p, encoding="utf-8", errors="replace").read()
        print(f"\n##### {fn[:56]}  {len(t)}c")
        print(f"  题号行={len(Q.findall(t))}  选项起行={len(OPT.findall(t))}  "
              f"答案标记={len(ANS.findall(t))}  独占字母行={len(LONE.findall(t))}")
        lines = [l for l in t.split("\n") if l.strip()]
        # 展示一段含选项的片段
        shown = 0
        for i, l in enumerate(lines):
            if OPT.match(l):
                print("  --- 选项片段 ---")
                for l2 in lines[max(0, i - 4):i + 6]:
                    print("  | " + l2[:104])
                shown += 1
                if shown >= 1:
                    break
        if not shown:
            print("  （未发现任何选项起行）")
            for l in lines[40:52]:
                print("  ? " + l[:104])
    return 0


if __name__ == "__main__":
    sys.exit(main())

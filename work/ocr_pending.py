#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""列出已 OCR 但尚未进入题库的文本，量化“待吸收”的 OCR 产出。"""
import json
import os
import sys

WORK = os.path.dirname(os.path.abspath(__file__))
OCR = os.path.join(WORK, "ocr")

qs = json.load(open(os.path.join(WORK, "bank", "questions.json"), encoding="utf-8"))["questions"]
used = {os.path.splitext(os.path.basename(q["sourceFile"]))[0] for q in qs if q.get("sourceFile")}

pending, empty = [], []
for dp, _dn, fs in os.walk(OCR):
    for fn in fs:
        if not fn.endswith(".txt"):
            continue
        stem = os.path.splitext(fn)[0]
        size = os.path.getsize(os.path.join(dp, fn))
        if stem not in used:
            (empty if size < 2000 else pending).append((size, fn, dp))

print(f"题库已引用 OCR 文本 {len(used & {os.path.splitext(f)[0] for _, f, _ in [(0, x, 0) for x in []]} | used)} 个来源名")
print(f"\n已 OCR 但未进入题库（≥2KB，共 {len(pending)} 个）：")
for size, fn, dp in sorted(pending, reverse=True):
    print(f"  {size:8d}B  {fn[:66]}")
print(f"\n疑似无题目内容（<2KB，共 {len(empty)} 个）：")
for size, fn, dp in sorted(empty, reverse=True)[:12]:
    print(f"  {size:8d}B  {fn[:66]}")

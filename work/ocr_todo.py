#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""对照 ocr.py 的候选集与 manifest：还有多少扫描件从未进入 OCR 队列。"""
import json
import os
import sys
from collections import Counter

WORK = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, WORK)
import ocr  # noqa: E402

cands = ocr.collect(260.0)
man = json.load(open(os.path.join(WORK, "ocr", "manifest.json"), encoding="utf-8"))
done = {m["src"] for m in man if m.get("status") == "ok"}
errd = {m["src"] for m in man if m.get("status") == "error"}

print(f"扫描件候选总数：{len(cands)}")
print(f"分级分布：{dict(sorted(Counter(x['tier'] for x in cands).items()))}")
print(f"manifest 记录 {len(man)}（成功 {len(done)}，失败 {len(errd)}）")
todo = [x for x in cands if x["src"] not in done]
print(f"候选里尚未成功的：{len(todo)}\n")

for x in sorted(todo, key=lambda y: (y["tier"], -y["size_mb"])):
    rel = os.path.relpath(x["src"], ocr.ROOT)
    print(f"  T{x['tier']} {x['size_mb']:7.1f}MB  {rel[:92]}")

print(f"\nmanifest 中失败的文件：")
for m in man:
    if m.get("status") == "error":
        print(f"  {os.path.relpath(m['src'], ocr.ROOT)[:92]}  :: {m.get('error')}")

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Detect answer/option marker patterns across extracted text files."""
import glob
import os
import re

ROOT = r"D:\app project\work"
PATS = {
    "【答案】": re.compile(r"【答案】"),
    "答案:": re.compile(r"答案[:：]"),
    "参考答案": re.compile(r"参考答案"),
    "解析": re.compile(r"解析"),
    "linestart_A": re.compile(r"(?m)^\s*A[．.、]"),
    "num_q": re.compile(r"(?m)^\s*\d+[．.、]"),
}

rows = []
for d in ("text", "text2", "text3"):
    for p in sorted(glob.glob(os.path.join(ROOT, d, "**", "*.txt"), recursive=True)):
        try:
            t = open(p, encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        if len(t) < 3000:
            continue
        counts = {k: len(v.findall(t)) for k, v in PATS.items()}
        rows.append((os.path.relpath(p, ROOT), counts))

for rel, c in rows:
    print(f"{rel:78s} A={c['linestart_A']:5d} q={c['num_q']:5d} ans={c['【答案】']:5d} "
          f"ansColon={c['答案:']:5d} ref={c['参考答案']:5d} expl={c['解析']:5d}")

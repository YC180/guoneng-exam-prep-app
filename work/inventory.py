#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Produce a compact, human-readable inventory of the reference material tree."""
import os
import sys
from collections import defaultdict

ROOT = sys.argv[1] if len(sys.argv) > 1 else r"D:\DOWNLOADS\26国家能源集团通关资料"
OUT = sys.argv[2] if len(sys.argv) > 2 else r"D:\app project\work\inventory.txt"

groups = defaultdict(list)
for dirpath, _d, filenames in os.walk(ROOT):
    for n in filenames:
        p = os.path.join(dirpath, n)
        rel = os.path.relpath(p, ROOT)
        top = rel.split(os.sep)[0]
        groups[top].append((rel, os.path.getsize(p)))

lines = []
for top in sorted(groups, key=lambda t: t):
    files = sorted(groups[top])
    total = sum(s for _r, s in files) / (1024 * 1024)
    lines.append(f"\n{'=' * 100}\n### {top}  ({len(files)} files, {total:.1f} MB)\n{'=' * 100}")
    for rel, size in files:
        lines.append(f"  {size / 1024:9.0f} KB  {rel[len(top) + 1:]}")

with open(OUT, "w", encoding="utf-8") as fh:
    fh.write("\n".join(lines))
print(f"wrote {OUT}: {len(lines)} lines, {sum(len(v) for v in groups.values())} files")

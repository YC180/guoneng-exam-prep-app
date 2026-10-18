#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""从长文本中抽取“骨架”：章节标题 + 编号/冒号式关键条目。

用于在**不臆造内容**的前提下归纳长文档：只回显原文自己的标题与关键短句，
供人工（或模型）据此写摘要，避免把乱序文本当成知识点。
"""
import os
import re
import sys

WORK = os.path.dirname(os.path.abspath(__file__))

HEAD_RE = re.compile(r"^第[一二三四五六七八九十]+[节章]|^[一二三四五六七八九十]+、")
NUM_RE = re.compile(r"^\s*[（(]?\d{1,2}[）)、.．]")
KEY_RE = re.compile(r"^[^。；]{4,40}[：:]?$")


def main():
    rel = sys.argv[1]
    start = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    p = os.path.join(WORK, rel) if not os.path.isabs(rel) else rel
    lines = open(p, encoding="utf-8").read().split("\n")
    for i, raw in enumerate(lines[start - 1:], start):
        t = raw.strip()
        if not t or t.startswith("[[") or re.match(r"^第\d+页，共", t):
            continue
        if HEAD_RE.match(t) or NUM_RE.match(t) or (len(t) <= 34 and KEY_RE.match(t)):
            print(f"{i:5d}| {t[:100]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

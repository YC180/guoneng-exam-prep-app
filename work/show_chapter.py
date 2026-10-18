#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""抽查某章节的题目，人工确认解析质量。"""
import json
import os
import sys

WORK = os.path.dirname(os.path.abspath(__file__))
KEY = sys.argv[1] if len(sys.argv) > 1 else "2024年3月时政"
LIMIT = int(sys.argv[2]) if len(sys.argv) > 2 else 4

qs = json.load(open(os.path.join(WORK, "bank", "questions.json"), encoding="utf-8"))["questions"]
sel = [q for q in qs if KEY in (q.get("chapter") or "")][:LIMIT]
print(f"章节含“{KEY}”的题：共 " + str(sum(1 for q in qs if KEY in (q.get("chapter") or ""))) + f"，抽查 {len(sel)} 道\n")
for q in sel:
    print(f"{q['id']}  ans={'/'.join(q.get('answer') or [])}  {q['answerStatus']}  第{q.get('sourcePage')}页")
    print("  题干:", q["stem"][:120])
    for o in q.get("options") or []:
        print(f"    {o['key']}. {(o.get('text') or '')[:64]}")
    print("  解析:", (q.get("explanation") or "")[:80])
    print()

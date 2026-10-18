#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""按问题类型抽样查看具体题目，判断是真缺陷还是误报。"""
import json
import os
import sys
from collections import defaultdict

WORK = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, WORK)
from quality_audit import problems  # noqa: E402

BANK = os.path.join(WORK, "bank", "questions.json")
WANT = sys.argv[1] if len(sys.argv) > 1 else "选项数=3"
LIMIT = int(sys.argv[2]) if len(sys.argv) > 2 else 6


def main():
    qs = json.load(open(BANK, encoding="utf-8"))["questions"]
    hit = [(q, problems(q)) for q in qs]
    hit = [(q, ps) for q, ps in hit if WANT in ps]
    print(f"“{WANT}” 共 {len(hit)} 题，抽样 {LIMIT} 道：\n")
    for q, ps in hit[:LIMIT]:
        print(f"### {q['id']}  ans={'/'.join(q.get('answer') or [])}  status={q['answerStatus']}")
        print(f"    来源: {os.path.basename(q.get('sourceFile') or '')[:60]}  p{q.get('sourcePage')}")
        print(f"    题干: {q['stem'][:150]}")
        for o in q.get("options") or []:
            print(f"      {o['key']}. {(o.get('text') or '')[:80]}")
        print(f"    解析: {(q.get('explanation') or '')[:100]!r}")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())

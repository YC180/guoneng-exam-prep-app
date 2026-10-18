#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""试跑 OCR 题库解析器，检查切块质量与答案对应率。"""
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_bank as B  # noqa: E402


def main():
    found = B.discover_ocr_sources()
    print(f"发现可入库的 OCR 文本 {len(found)} 个\n")
    if not found:
        print("暂无（OCR 进行中）")
        return 0
    total = Counter()
    for rel, cat, ch, tags in found:
        p = os.path.join(B.OCR_DIR, rel)
        raw = open(p, encoding="utf-8", errors="replace").read()
        qs = B.parse_ocr_choice(B.clean_lines(raw), {})
        tc = Counter(q["answerStatus"] for q in qs)
        types = Counter(q["type"] for q in qs)
        total.update(tc)
        print(f"{os.path.basename(rel)[:46]:48s} {len(qs):5d} 题  "
              f"ok={tc.get('verified',0):4d} review={tc.get('needs_review',0):4d} "
              f"missing={tc.get('missing',0):4d}  题型={dict(types)}")
        for q in qs[:2]:
            print(f"    题干: {q['stem'][:70]}")
            print(f"    选项: {[o['key'] + '.' + o['text'][:12] for o in q['options']]}")
            print(f"    答案: {q['answer']}  解析: {q['explanation'][:60]!r}")
            print()
    print(f"合计 {sum(total.values())} 题：{dict(total)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

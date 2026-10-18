#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Diagnose why particular sources fail to get questions / answers."""
import os
import re
import sys

sys.path.insert(0, r"D:\app project\work")
import build_bank as bb  # noqa: E402


def diag(base, fname, label, n=14):
    p = os.path.join(base, fname)
    if not os.path.exists(p):
        print(f"### MISSING {fname}")
        return
    lines = bb.expand_inline_options(bb.clean_lines(open(p, encoding="utf-8", errors="replace").read()))
    starts = bb.question_starts(lines)
    ordered, by_no = bb.parse_answer_keys(lines)
    blocks = bb.parse_question_blocks(lines, {})
    print("=" * 100)
    print(f"### {label}: lines={len(lines)} starts={len(starts)} blocks={len(blocks)} "
          f"answerkeys={len(ordered)}")
    print("  first starts:", [(s[1], s[2][:34]) for s in starts[:6]])
    print("  first blocks:", [(b['no'], b['stem'][:40], len(b['options'])) for b in blocks[:4]])
    print("  first answerkeys:", [(k[0], k[1][0], k[1][1][:40]) for k in ordered[:6]])
    hits = [(i, l) for i, (l, _p) in enumerate(lines) if bb.ANS_ANY_RE.search(l)]
    print(f"  lines containing an answer marker: {len(hits)}")
    for i, l in hits[:n]:
        print(f"     [{i}] {l[:120]}")
    qn = [(i, l) for i, (l, _p) in enumerate(lines) if not bb.opt_of(l) and bb.QNUM_RE.match(l)][:8]
    print("  raw numbered-looking lines:")
    for i, l in qn:
        print(f"     [{i}] {l[:120]}")


T2 = r"D:\app project\work\text2"
diag(bb.TEXT, "2025国家能源校招笔试真题（不含英语）完整版答案及解释.txt", "2025真题(不含英语)")
diag(bb.TEXT2, r"【全国时政】全国时政热点（已更4月）\24-26年时政\2026年时政+试题\2026年1月时政试题179道.txt", "2026年1月时政")
diag(bb.TEXT, r"EPI综合能力500题\EPI综合能力测试-数量关系-试题.txt", "EPI500数量关系")
diag(bb.TEXT2, r"【全国时政】全国时政热点（已更4月）\【重要会议】2025重要时政+文章考点\二十大相关资料\二十大试题（240题）.txt", "二十大240题")

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""题库质量审计：找出结构性缺陷（不是答案对错，而是“这题根本不成形”）。

输出 per-source 的问题率，便于定位是哪个解析器/哪份资料出的问题。
"""
import json
import os
import re
import sys
from collections import Counter, defaultdict

WORK = os.path.dirname(os.path.abspath(__file__))
BANK = os.path.join(WORK, "bank", "questions.json")

PAGE_LEAK = re.compile(r"\[\[\s*PAGE|#\s*SOURCE|#\s*OCR")
CIRCLED = re.compile(r"[\u2460-\u2473]")


def problems(q):
    out = []
    stem = (q.get("stem") or "").strip()
    opts = q.get("options") or []
    expl = q.get("explanation") or ""
    if len(stem) < 10:
        out.append("题干过短")
    if PAGE_LEAK.search(stem) or PAGE_LEAK.search(expl):
        out.append("页码/来源标记泄漏")
    if q["type"] in ("single_choice", "multiple_choice"):
        if len(opts) != 4:
            out.append(f"选项数={len(opts)}")
        keys = [o["key"] for o in opts]
        if len(set(keys)) != len(keys):
            out.append("选项键重复")
        texts = [(o.get("text") or "").strip() for o in opts]
        if any(not t for t in texts):
            out.append("空选项文本")
        if len(texts) == len(set(texts)) and len(texts) > 1 and len(set(texts)) == 1:
            out.append("选项全同")
        elif texts and len(set(texts)) < len(texts):
            out.append("选项有重复")
        if any(re.match(r"^\d{2,}$", t) and CIRCLED.search(stem) for t in texts):
            out.append("圈号数字讹为阿拉伯数字")
    if stem.endswith(("（", "(")):
        out.append("题干括号未闭合")
    # 无编号资料（unnumbered）容易把上一题的解析吸进题干
    if len(stem) > 80 and re.search(r"(故选|本题选择|正确答案|故答案|选择\s*[A-H]\s*选项)", stem):
        out.append("题干含上一题解析残留")
    return out


def main():
    qs = json.load(open(BANK, encoding="utf-8"))["questions"]
    per_src = defaultdict(Counter)
    overall = Counter()
    flagged = []
    for q in qs:
        ps = problems(q)
        if ps:
            flagged.append((q, ps))
            for p in ps:
                overall[p] += 1
            per_src[q.get("sourceFile") or "?"].update(ps)
    print(f"题库 {len(qs)} 题，有结构问题的 {len(flagged)} 题（{len(flagged)/len(qs)*100:.1f}%）\n")
    print("问题类型汇总：")
    for p, c in overall.most_common():
        print(f"  {c:6d}  {p}")
    print("\n问题最多的来源（前 15）：")
    rows = sorted(per_src.items(), key=lambda x: -sum(x[1].values()))
    for s, c in rows[:15]:
        tot = sum(1 for q in qs if q.get("sourceFile") == s)
        print(f"  {sum(c.values()):6d}/{tot:5d}  {os.path.basename(s)[:56]}")
        print(f"          {dict(c)}")
    print("\n抽样 8 道问题题：")
    for q, ps in flagged[:8]:
        print(f"  [{','.join(ps)}] {q['id']} ({q['type']}) ans={'/'.join(q.get('answer') or [])}")
        print(f"    stem: {q['stem'][:90]}")
        print(f"    opts: {[(o['key'], (o.get('text') or '')[:14]) for o in (q.get('options') or [])]}")

    out = {
        "total": len(qs),
        "flagged": len(flagged),
        "rate": round(len(flagged) / len(qs), 4) if qs else None,
        "byIssue": dict(overall),
        "bySource": [
            {"sourceFile": s, "total": sum(1 for q in qs if q.get("sourceFile") == s),
             "problems": dict(c), "problemCount": sum(c.values())}
            for s, c in rows[:40]
        ],
        "note": ("结构性缺陷指“这题不成形”（选项缺失/重复、题干过短或含上一题解析残留等），"
                 "不代表答案对错。答案对错的核对见 validation_report.json 的 answerCrossCheck。"),
    }
    with open(os.path.join(WORK, "bank", "quality_audit.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    print("\n写出 work/bank/quality_audit.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())

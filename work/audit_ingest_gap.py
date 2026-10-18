#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""审计「已读但未入库」的语料，找出被规则漏掉的可用题源。

为什么要做：OCR 出来的文本里，只有匹配 `OCR_RULES`（或时政月份兜底）的文件会被
解析进题库，**其余一律跳过**。跳过是必要的（讲义/知识类本就不该出题），
但如果某个文件其实能稳定产出大量题目却被跳过，那就是**静默丢弃了可用内容**。

本脚本对每个 OCR 文本试跑全部解析器，与题库里实际出现的来源文件名对比，
列出「能出题 ≥ 阈值、但题库中一道都没有」的文件，并给出采纳率，
以便区分两种情况：真该跳过（讲义/图片题） vs 规则漏掉（应补入）。

用法：python audit_ingest_gap.py [--min 30]
"""
import json
import os
import sys

WORK = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, WORK)
import build_bank as B  # noqa: E402

BANK = os.path.join(WORK, "bank")
OCR_DIR = os.path.join(WORK, "ocr")


def trial(raw, is_ocr):
    lines = B.ocr_lines(raw) if is_ocr else B.clean_lines(raw)
    exp = B.expand_inline_options(
        [(B.normalize_bare_option_letters(t), pg) for t, pg in lines])
    res = {}
    res["numbered"] = B.parse_numbered(exp, {})
    if is_ocr:
        res["ocr_choice"] = B.parse_ocr_choice(lines, {})
        res["ocr_sectioned"] = B.parse_ocr_sectioned(exp, {})
    res["unnumbered"] = B.parse_unnumbered(exp, {})
    name, qs = max(res.items(),
                   key=lambda kv: (len(kv[1]),
                                   sum(1 for q in kv[1] if q.get("answerStatus") == "verified")))
    ver = sum(1 for q in qs if q.get("answerStatus") == "verified")
    return name, len(qs), ver


def main():
    min_yield = 30
    if "--min" in sys.argv:
        min_yield = int(sys.argv[sys.argv.index("--min") + 1])

    bank = json.load(open(os.path.join(BANK, "questions.json"), encoding="utf-8"))["questions"]
    ingested = {os.path.basename((q.get("sourceFile") or "").strip()) for q in bank}
    ingested = {x for x in ingested if x}
    print(f"题库 {len(bank)} 题，来自 {len(ingested)} 个文件\n")

    rows = []
    for dp, _dn, fs in os.walk(OCR_DIR):
        for fn in fs:
            if not fn.endswith(".txt") or fn.startswith("_"):
                continue
            p = os.path.join(dp, fn)
            raw = open(p, encoding="utf-8", errors="replace").read()
            mode, n, ver = trial(raw, True)
            already = fn in ingested
            rows.append((already, n, ver, mode, fn, os.path.relpath(p, OCR_DIR), len(raw)))

    gap = [r for r in rows if not r[0] and r[1] >= min_yield]
    gap.sort(key=lambda r: -r[2])
    print(f"OCR 文本 {len(rows)} 份；其中**未入库**且试解析能出题 ≥{min_yield} 的：{len(gap)} 份\n")
    if gap:
        print(f"{'题数':>5} {'已验证':>6} {'采纳率':>7} {'方式':<13} 文件")
        for _a, n, ver, mode, fn, rel, _c in gap:
            rate = ver / n if n else 0
            print(f"{n:5d} {ver:6d} {rate*100:6.1f}% {mode:<13} {rel[:86]}")
    print()
    print(f"（已入库的 OCR 文本 {sum(1 for r in rows if r[0])} 份，"
          f"未入库且出题 <{min_yield} 的 {sum(1 for r in rows if not r[0] and r[1] < min_yield)} 份"
          f" —— 后者多为讲义/知识类或纯图片题，按设计本就跳过）")
    out = [{"file": r[5], "alreadyIngested": r[0], "parsed": r[1], "verified": r[2],
            "mode": r[3], "chars": r[6]} for r in rows]
    json.dump(out, open(os.path.join(BANK, "ingest_gap_audit.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("写出 work/bank/ingest_gap_audit.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())

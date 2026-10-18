#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""对单个 OCR/提取文本试跑题库解析，确认它能否产出题目（不写题库）。

用法：python try_parse.py <相对 ROOT 的路径或 stem>
"""
import os
import sys

WORK = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, WORK)
import build_bank as B  # noqa: E402


def locate(name):
    """在 text*/ocr/ocr_ordered/text6 里按 stem 找到文本，取**最大**的一份。

    同名的提取文本可能是近乎空的占位（几百字符），而 OCR 产出才是正文，
    所以必须比大小，不能拿到第一个就返回。
    """
    stem = os.path.splitext(os.path.basename(name))[0]
    best = None
    for d in ("text", "text2", "text3", "text4", "text5", "text6", "text7", "ocr", "ocr_ordered"):
        base = os.path.join(WORK, d)
        if not os.path.isdir(base):
            continue
        for dp, _dn, fs in os.walk(base):
            for fn in fs:
                if fn.endswith(".txt") and os.path.splitext(fn)[0] == stem:
                    p = os.path.join(dp, fn)
                    size = os.path.getsize(p)
                    if best is None or size > best[1]:
                        best = (p, size)
    return best[0] if best else None


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    p = locate(sys.argv[1])
    if not p:
        print("找不到文本：", sys.argv[1])
        return 1
    raw = open(p, encoding="utf-8", errors="replace").read()
    print("文件:", os.path.relpath(p, WORK), f"({len(raw)} 字符)")

    ocr = "OCR" in raw[:400] or p.find("ocr") >= 0
    lines = B.ocr_lines(raw) if ocr else B.clean_lines(raw)
    exp = B.expand_inline_options([(B.normalize_bare_option_letters(t), pg) for t, pg in lines])

    res = {}
    res["numbered"] = B.parse_numbered(exp, {})
    if ocr:
        res["ocr_choice"] = B.parse_ocr_choice(lines, {})
        res["ocr_sectioned"] = B.parse_ocr_sectioned(exp, {})
        res["ocr_keyed"] = B.parse_numbered(B.inject_compact_answer_keys(exp), {})
    res["unnumbered"] = B.parse_unnumbered(exp, {})

    for k, v in res.items():
        verified = sum(1 for q in v if q.get("answerStatus") == "verified")
        print(f"  {k:14s} 题数 {len(v):5d} 已验证 {verified:5d}")
    best = max(res.items(), key=lambda kv: (len(kv[1]), sum(1 for q in kv[1] if q.get("answerStatus") == "verified")))
    print("\n最佳解析方式:", best[0], "题数", len(best[1]))
    for q in best[1][:4]:
        print(f"  - [{q['answerStatus']}] {'/'.join(q['answer'])} | {q['stem'][:80]}")
        for o in q["options"]:
            print(f"      {o['key']}. {o['text'][:60]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

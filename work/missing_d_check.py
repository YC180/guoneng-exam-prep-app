#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""对“只有 A/B/C 三个选项”的题目，回到原始资料里查证 D 选项是否真的存在。"""
import json
import os
import sys
from collections import Counter

WORK = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, WORK)
import build_bank as B  # noqa: E402

QS = json.load(open(os.path.join(WORK, "bank", "questions.json"), encoding="utf-8"))["questions"]


def raw_for(srcname):
    """按源文件名在 text/text2/text5/ocr 里找原提取文本。"""
    stem = os.path.splitext(srcname)[0]
    for d in ("text", "text2", "text5", "ocr", "text4", "text6", "text7"):
        for dp, _dn, fs in os.walk(os.path.join(WORK, d)):
            for fn in fs:
                if os.path.splitext(fn)[0] == stem:
                    return os.path.join(dp, fn)
    return None


def main():
    three = [q for q in QS if q.get("type") == "single_choice" and len(q.get("options") or []) == 3
             and "".join(o["key"] for o in q["options"]) == "ABC"]
    print(f"ABC 三选项题 {len(three)} 道\n")
    checked = found = 0
    per_src = Counter()
    for q in three[:400]:
        p = raw_for(os.path.basename(q["sourceFile"]))
        if not p:
            continue
        t = open(p, encoding="utf-8", errors="replace").read()
        key = q["stem"][:18].replace(" ", "")
        idx = t.replace(" ", "").find(key)
        if idx < 0:
            continue
        checked += 1
        # 取原文中该题后 600 字符，看有没有 D 选项
        window = t.replace(" ", "")[idx:idx + 700]
        if "D." in window or "D．" in window or "D、" in window:
            D = window.find("D.")
            if D < 0:
                D = window.find("D．")
            found += 1
            per_src[os.path.basename(q["sourceFile"])] += 1
            if found <= 3:
                print(f"--- 原资料中 D 存在但未入库：{q['id']}")
                print(f"    入库选项: {[(o['key'], o['text'][:20]) for o in q['options']]}")
                print(f"    原文片段: ...{window[D-90:D+60]}")
                print()
    print(f"核对 {checked} 题，其中 {found} 题原资料里确实有 D 选项但入库时丢失")
    if per_src:
        print("按来源：", dict(per_src.most_common(8)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

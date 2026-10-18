#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""OCR 题目自洽性复核。

思路：OCR 出的解析原文里通常带有“因此，选择D选项”“故本题选C”这类结论句，
这是**独立于答案行**的另一处答案信息。若两者不一致，说明其中一处被 OCR 认错，
该题不应继续当作“答案已核实”，应降级为 needs_review。

输出：各类统计 + 不一致题目清单，供人工抽查。
"""
import json
import os
import re
import sys
from collections import Counter

WORK = os.path.dirname(os.path.abspath(__file__))
BANK = os.path.join(WORK, "bank", "questions.json")
OUT = os.path.join(WORK, "bank", "ocr_selfcheck.json")

import build_bank as B  # noqa: E402

# 解析中的结论句（与构建阶段共用同一套正则，避免口径漂移）
CONCL_RES = B.OCR_CONCL_RES


def concl_letters(expl: str):
    found = []
    for rx in CONCL_RES:
        for m in rx.finditer(expl or ""):
            found.append(m.group(1).upper())
    return found


def main():
    data = json.load(open(BANK, encoding="utf-8"))
    qs = data["questions"]
    ocr = [q for q in qs if "OCR" in (q.get("tags") or [])]
    print(f"题库 {len(qs)} 题，其中 OCR 题 {len(ocr)} 题")

    stat = Counter()
    mismatch = []
    for q in ocr:
        ans = [str(a).upper() for a in (q.get("answer") or [])]
        letters = concl_letters(q.get("explanation") or "")
        uniq = sorted(set(letters))
        if not letters:
            stat["解析无结论句（无法自洽复核）"] += 1
            continue
        if len(uniq) > 1:
            stat["解析结论句自相矛盾"] += 1
            continue
        if not ans:
            stat["题目无答案但解析有结论"] += 1
            continue
        if ans == uniq:
            stat["答案与解析结论一致 ✅"] += 1
        else:
            stat["答案与解析结论不一致 ❌"] += 1
            mismatch.append({
                "id": q["id"], "sourceFile": q["sourceFile"], "sourcePage": q.get("sourcePage"),
                "stem": q["stem"][:100], "answer": ans, "explanationSays": uniq,
                "answerStatus": q["answerStatus"], "chapter": q["chapter"],
            })

    total_checked = stat["答案与解析结论一致 ✅"] + stat["答案与解析结论不一致 ❌"]
    print()
    for k, v in stat.most_common():
        print(f"  {k}: {v}")
    if total_checked:
        rate = stat["答案与解析结论一致 ✅"] / total_checked
        print(f"\n可自洽复核 {total_checked} 题，一致率 {rate*100:.2f}%")

    print(f"\n不一致题目 {len(mismatch)} 条（示例前 15 条）：")
    for m in mismatch[:15]:
        print(f"  {m['id']} 答案={m['answer']} 解析说={m['explanationSays']} "
              f"状态={m['answerStatus']} 页码={m['sourcePage']}")
        print(f"      {m['stem']}")

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump({"checked": total_checked, "stats": dict(stat),
                   "mismatch": mismatch}, fh, ensure_ascii=False, indent=1)
    print(f"\n写出 {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

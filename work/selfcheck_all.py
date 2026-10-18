#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""全库答案自洽性复核（不只 OCR）。

原理：很多资料的解析里带有独立的结论句（"因此，选择D选项"/"故本题选C"）。
把它与题目解析出的 answer 比对：
  - 一致 → 该题答案有第二处独立佐证
  - 不一致 → 极可能是**题号与答案错位**或答案字段解析错误，必须降级为 needs_review

按来源文件汇总，便于定位是哪一份资料解析有问题。
输出：work/bank/selfcheck_all.json
"""
import json
import os
import re
import sys
from collections import Counter, defaultdict

WORK = os.path.dirname(os.path.abspath(__file__))
BANK = os.path.join(WORK, "bank", "questions.json")
OUT = os.path.join(WORK, "bank", "selfcheck_all.json")

CONCL_RES = [
    re.compile(r"选择\s*([A-Ha-h])\s*选项"),
    re.compile(r"故选\s*([A-Ha-h])"),
    re.compile(r"故本题\s*选\s*([A-Ha-h])"),
    re.compile(r"本题\s*选\s*([A-Ha-h])"),
    re.compile(r"应选\s*([A-Ha-h])"),
    re.compile(r"正确答案\s*(?:为|是)?\s*([A-Ha-h])"),
    re.compile(r"选\s*([A-Ha-h])\s*项"),
    re.compile(r"答案\s*(?:为|是)\s*([A-Ha-h])\b"),
    re.compile(r"【\s*答\s*案\s*】\s*([A-Ha-h])"),
]


def concl(expl):
    out = []
    for rx in CONCL_RES:
        out += [m.group(1).upper() for m in rx.finditer(expl or "")]
    return out


def main():
    data = json.load(open(BANK, encoding="utf-8"))
    qs = data["questions"]
    print(f"题库 {len(qs)} 题，开始全库自洽复核\n")

    stat = Counter()
    mism = []
    per_src = defaultdict(lambda: {"ok": 0, "bad": 0, "none": 0})
    for q in qs:
        ans = [str(a).upper() for a in (q.get("answer") or [])]
        letters = concl(q.get("explanation") or "")
        uniq = sorted(set(letters))
        src = q.get("sourceFile") or "?"
        if not letters:
            stat["解析无独立结论句"] += 1
            per_src[src]["none"] += 1
            continue
        if len(uniq) > 1:
            stat["解析结论句本身矛盾（多字母）"] += 1
            per_src[src]["none"] += 1
            continue
        if not ans:
            stat["题目无答案但解析有结论"] += 1
            per_src[src]["none"] += 1
            continue
        if ans == uniq:
            stat["答案与解析结论一致 ✅"] += 1
            per_src[src]["ok"] += 1
        else:
            stat["答案与解析结论不一致 ❌"] += 1
            per_src[src]["bad"] += 1
            mism.append({
                "id": q["id"], "sourceFile": src, "sourcePage": q.get("sourcePage"),
                "chapter": q.get("chapter"), "stem": q["stem"][:90],
                "answer": ans, "explanationSays": uniq, "answerStatus": q["answerStatus"],
            })

    checked = stat["答案与解析结论一致 ✅"] + stat["答案与解析结论不一致 ❌"]
    for k, v in stat.most_common():
        print(f"  {k}: {v}")
    if checked:
        print(f"\n有独立佐证 {checked} 题，一致率 {stat['答案与解析结论一致 ✅']/checked*100:.2f}%")

    print(f"\n不一致 {len(mism)} 条，按来源汇总:")
    rows = [(s, d) for s, d in per_src.items() if d["bad"] > 0]
    rows.sort(key=lambda x: -x[1]["bad"])
    for s, d in rows[:30]:
        print(f"  bad={d['bad']:4d} ok={d['ok']:4d} none={d['none']:4d}  {os.path.basename(s)[:60]}")

    json.dump({"checked": checked, "stats": dict(stat), "bySource": {k: v for k, v in per_src.items()},
               "mismatch": mism},
              open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n写出 {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

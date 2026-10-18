#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""查询题库中某主题的题目，并核对它们的答案与解析是否自洽。"""
import json
import os
import re
import sys

WORK = os.path.dirname(os.path.abspath(__file__))
BANK = os.path.join(WORK, "bank", "questions.json")
CONCL = [re.compile(p) for p in [
    r"选择\s*([A-Ha-h])\s*选项", r"故选\s*([A-Ha-h])", r"【\s*答\s*案\s*】\s*([A-Ha-h])"]]

KEY = sys.argv[1] if len(sys.argv) > 1 else "一号文件"


def main():
    qs = json.load(open(BANK, encoding="utf-8"))["questions"]
    hit = [q for q in qs if KEY in (q.get("chapter") or "") or KEY in (q.get("sourceFile") or "")
           or KEY in (q.get("stem") or "")[:60]]
    print(f"含“{KEY}”的题目 {len(hit)} 道")
    from collections import Counter
    print("按来源：")
    for s, n in Counter(q["sourceFile"] for q in hit).most_common():
        print(f"  {n:4d}  {os.path.basename(s)}")
    print("\n按章节：")
    for s, n in Counter(q.get("chapter") for q in hit).most_common(12):
        print(f"  {n:4d}  {s}")
    ok = bad = 0
    print("\n前 6 题抽查：")
    for q in hit[:6]:
        letters = []
        for rx in CONCL:
            letters += [m.group(1).upper() for m in rx.finditer(q.get("explanation") or "")]
        u = sorted(set(letters))
        verdict = ""
        if len(u) == 1:
            if [str(a).upper() for a in (q.get("answer") or [])] == u:
                ok += 1
                verdict = "  ↔解析一致 ✅"
            else:
                bad += 1
                verdict = f"  ↔解析说{u} ❌"
        print(f"  {q['id']} ans={'/'.join(q.get('answer') or [])} {q['answerStatus']}{verdict}")
        print(f"      {q['stem'][:78]}")
        print(f"      解析: {(q.get('explanation') or '')[:70]!r}")
    print(f"\n抽查中一致 {ok}，冲突 {bad}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

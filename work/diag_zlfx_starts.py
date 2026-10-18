#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""查清「资料分析学生版」为何只解析出 56 题：`question_starts` 到底拒绝了哪些题号行。"""
import os
import re
import sys

WORK = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, WORK)
import build_bank as B  # noqa: E402

P = os.path.join(WORK, "text7", "国家能源秋招常考易错1000题-资料分析-学生版.txt")


def main():
    raw = open(P, encoding="utf-8", errors="replace").read()
    lines = B.expand_inline_options(B.clean_lines(raw))
    print("总行数:", len(lines))

    # 用宽松正则找出所有“看似题号行”
    loose = re.compile(r"^\s*(\d{1,3})\s*[.、]\s*(\S.*)$")
    cand = [(i, int(m.group(1)), m.group(2)) for i, (t, _p) in enumerate(lines)
            for m in [loose.match(t)] if m]
    nums = [c[1] for c in cand]
    print(f"宽松匹配题号行: {len(cand)} 个；不同题号 {len(set(nums))} 个；"
          f"最小 {min(nums)} 最大 {max(nums)}")
    from collections import Counter
    dup = {n: c for n, c in Counter(nums).items() if c > 1}
    print(f"重复题号 {len(dup)} 个，例：{list(dup.items())[:12]}")

    starts = B.question_starts(lines)
    sn = [no for _si, no, _h in starts]
    print(f"\nquestion_starts 认可: {len(starts)} 个；题号 {sn[:20]} ...")
    accepted = set()
    for si, no, _h in starts:
        accepted.add(si)
    rejected = [(i, n, h) for i, n, h in cand if i not in accepted]
    print(f"\n被拒绝的题号行 {len(rejected)} 个，前 12 个：")
    for i, n, h in rejected[:12]:
        print(f"  行{i:5d} 题号{n:4d} 「{h[:64]}」")

    # 看这些被拒行的相邻上下文（是否位于材料段落中/是否被上题选项吞掉）
    print("\n被拒行附近上下文（取第 2 个被拒行）：")
    if len(rejected) > 1:
        i = rejected[1][0]
        for k in range(max(0, i - 4), min(len(lines), i + 3)):
            mark = "  <<< 被拒题号行" if k == i else ""
            print(f"  行{k:5d} |{lines[k][0][:66]}|{mark}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

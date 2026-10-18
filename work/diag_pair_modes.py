#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""对比 7 组配对来源：普通「按题号」解析 vs「分段」解析，并做自洽复核。

自洽复核：解析末尾常写「故本题答案为 X」等结论；把结论字母与答案字段比对，
矛盾率高的口径不可信（此前一号文件就是这么被判掉的）。
"""
import os
import re
import sys

WORK = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, WORK)
import build_bank as B  # noqa: E402

END_ANS_RE = re.compile(
    r"(?:故本题答案为|本题答案为|故答案为|答案选|应选|正确答案为|正确答案是|故选|因此选|故选择)"
    r"\s*([A-Ha-h])")


def selfcheck(qs):
    ck = cf = 0
    samples = []
    for q in qs:
        m = None
        for m2 in END_ANS_RE.finditer(q.get("explanation") or ""):
            m = m2
        if not m:
            continue
        ck += 1
        concl = m.group(1).upper()
        got = [str(x).upper() for x in (q.get("answer") or [])
               if re.fullmatch(r"[A-H]", str(x).upper())]
        if got and concl not in got:
            cf += 1
            if len(samples) < 2:
                samples.append((q.get("stem", "")[:48], "|".join(got), concl))
    return ck, cf, samples


def main():
    base = os.path.join(WORK, "text7")
    print(f"{'章节':<26}{'普通':>6}{'严格':>6}{'普通/可比':>9}{'普通/矛盾':>9}"
          f"{'严格/可比':>9}{'严格/矛盾':>9}")
    for _b, qf, af, _cat, ch, _tags in B.SOURCES_PAIR:
        qp, ap = os.path.join(base, qf), os.path.join(base, af)
        normal = B.parse_pair(qp, ap, {})
        sect = B.parse_pair_strict(qp, ap, {}, label=ch)
        nc, nf, ns = selfcheck(normal)
        sc, sf, ss = selfcheck(sect)
        print(f"{ch:<26}{len(normal):>6}{len(sect):>6}{nc:>9}{nf:>9}{sc:>9}{sf:>9}")
        for stem, got, concl in (ns + ss)[:2]:
            print(f"      ⚠️ 「{stem}」答案={got} 解析结论={concl}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

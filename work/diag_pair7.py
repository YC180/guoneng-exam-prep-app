#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""验证 F 目录 7 组「学生版 + 答案版」配对来源的解析质量（不写题库）。

为什么要专门验：此前 `【模拟试题】2025年中央一号文件` 的题目/答案文件**题号错位**，
解析器按位置配对得到错误答案，因此被判定不可靠、不予接入。新加入的 7 组必须
逐组通过同样的自洽复核，才能进题库。

自洽复核口径：题目解析文末常写「故本题答案为 X」/「故选 X」/「答案为 X」。
把解析里出现的结论字母与**答案字段**比对：
  - 一致 → 该题可信；
  - 不一致 → 疑似题号错位/答案错配，必须报出来。
"""
import os
import re
import sys
from collections import Counter

WORK = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, WORK)
import build_bank as B  # noqa: E402

END_ANS_RE = re.compile(
    r"(?:故本题答案为|本题答案为|故答案为|答案为|正确答案为|正确答案是|故选|因此选|故选择)"
    r"\s*([A-Ha-h])")


def main():
    rows = []
    total_out = 0
    total_ver = 0
    total_conflict = 0
    for base, qf, af, cat, ch, tags in B.SOURCES_PAIR:
        qp = os.path.join(WORK, base, qf)
        ap = os.path.join(WORK, base, af)
        ok = True
        for p in (qp, ap):
            if not os.path.exists(p):
                print(f"❌ 缺文件 {p}")
                ok = False
        if not ok:
            continue
        qlines = B.expand_inline_options(
            B.clean_lines(open(qp, encoding="utf-8", errors="replace").read()))
        alines = B.clean_lines(open(ap, encoding="utf-8", errors="replace").read())
        qs = B.parse_numbered_qfile(qlines)
        ans = B.parse_numbered_afile(alines)
        inter = set(qs) & set(ans)
        out = B.parse_pair(qp, ap, {})
        ver = sum(1 for q in out if q.get("answerStatus") == "verified")

        # 自洽复核：解析结论字母 vs 答案字段
        conflict = 0
        checked = 0
        samples = []
        for q in out:
            expl = q.get("explanation") or ""
            m = None
            for m2 in END_ANS_RE.finditer(expl):
                m = m2                     # 取最后一次结论
            if not m:
                continue
            checked += 1
            concl = m.group(1).upper()
            got = [str(a).upper() for a in (q.get("answer") or []) if re.fullmatch(r"[A-H]", str(a).upper())]
            if got and concl not in got:
                conflict += 1
                if len(samples) < 2:
                    samples.append((q.get("stem", "")[:56], "|".join(got), concl))
        total_out += len(out)
        total_ver += ver
        total_conflict += conflict
        rows.append((ch, len(qs), len(ans), len(inter), len(out), ver, checked, conflict, samples))
        flags = os.path.basename(qp)[:40]
        print(f"\n【{ch}】{flags}")
        print(f"  题目文件题号 {len(qs)} 个｜答案文件题号 {len(ans)} 个｜交集 {len(inter)} 个")
        print(f"  产出 {len(out)} 题（已核对 {ver}）")
        print(f"  自洽复核：可比对 {checked} 题，解析结论与答案字段**矛盾 {conflict} 题**"
              + ("  ✅" if conflict == 0 else "  ⚠️ 需人工判定"))
        for stem, got, concl in samples:
            print(f"     ⚠️ 题干「{stem}」答案字段={got} 而解析结论={concl}")

    print("\n" + "=" * 70)
    print(f"合计：产出 {total_out} 题（已核对 {total_ver}）；矛盾 {total_conflict} 题")
    print("核对表：")
    print(f"{'章节':<28}{'题干号':>7}{'答案号':>7}{'交集':>6}{'产出':>7}{'已核对':>7}{'可比对':>7}{'矛盾':>6}")
    for ch, nq, na, ni, no, ver, ck, cf, _s in rows:
        print(f"{ch:<28}{nq:>7}{na:>7}{ni:>6}{no:>7}{ver:>7}{ck:>7}{cf:>6}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

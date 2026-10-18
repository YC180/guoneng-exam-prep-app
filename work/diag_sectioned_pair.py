#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""诊断「分段重排题号」的配对文件（资料分析这类『材料 + 每组题号从 1 重来』的形态）。

问题：`parse_numbered_qfile` 以题号为字典键，而材料分析题**每组题号都从 1 重新开始**，
      后出现的组会覆盖前面的组 —— 实测资料分析学生版有 295 个题号行，却只留下 56 题，
      更糟的是「按题号取答案」会把不同组的题与答案错配（答案版是全局连续编号）。

本脚本实测两条口径，看哪条自洽：
  A) 按题号配对（现状）
  B) **文档顺序配对**：学生版按出现顺序取题，答案版按全局编号顺序取答案，逐位对应；
     并用「解析结论字母 vs 答案字段」做自洽复核（结论矛盾的题必须极少）。
另检测 2021 学生版是否**本身就只有 33 题**（而非漏解析）。
"""
import os
import re
import sys

WORK = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, WORK)
import build_bank as B  # noqa: E402

END_ANS_RE = re.compile(
    r"(?:故本题答案为|本题答案为|故答案为|答案为|正确答案为|正确答案是|故选|因此选|故选择)"
    r"\s*([A-Ha-h])")


def selfcheck(pairs):
    """返回（可比对数, 矛盾数, 矛盾样例）"""
    ck = cf = 0
    samples = []
    for q, (a, expl, _pg) in pairs:
        m = None
        for m2 in END_ANS_RE.finditer(expl or ""):
            m = m2
        if not m:
            continue
        ck += 1
        concl = m.group(1).upper()
        got = [str(x).upper() for x in (q.get("answer") or []) if re.fullmatch(r"[A-H]", str(x).upper())]
        if got and concl not in got:
            cf += 1
            if len(samples) < 3:
                samples.append((q.get("stem", "")[:50], "|".join(got), concl))
    return ck, cf, samples


def main():
    base = os.path.join(WORK, "text7")
    for qf, af, label in (
        ("国家能源秋招常考易错1000题-资料分析-学生版.txt",
         "国家能源秋招常考易错1000题-资料分析-答案版.txt", "资料分析"),
        ("2021年国家能源集团春季校园招聘笔试题-学生.txt",
         "2021年国家能源集团春季校园招聘笔试题-答案.txt", "2021春季校招"),
    ):
        qp, ap = os.path.join(base, qf), os.path.join(base, af)
        qlines = B.expand_inline_options(
            B.clean_lines(open(qp, encoding="utf-8", errors="replace").read()))
        alines = B.clean_lines(open(ap, encoding="utf-8", errors="replace").read())

        qdict = B.parse_numbered_qfile(qlines)          # A：按题号（会覆盖）
        ans = B.parse_numbered_afile(alines)            # 全局题号 → (答案, 解析, 页)
        seq = B.parse_numbered(qlines, {})              # B：文档顺序（列表，允许重号）

        print("=" * 74)
        print(f"【{label}】")
        print(f"  按题号解析（A）：{len(qdict)} 题（题号被覆盖）")
        print(f"  文档顺序解析（B）：{len(seq)} 题")
        print(f"  答案文件：{len(ans)} 条（题号 {min(ans)}~{max(ans)}）")
        # 学生版里有多少个「题号行」（含重号）
        nums = [no for _si, no, _h in B.question_starts(qlines)]
        print(f"  学生版题号行 {len(nums)} 个，其中重复题号 "
              f"{len(nums) - len(set(nums))} 个（→ 说明题号确实重排）")

        # A 口径自洽
        pairsA = []
        for no in sorted(qdict):
            if no in ans:
                it = qdict[no]
                a, expl, pg = ans[no]
                q = B.make_question(it["stem"], it["options"], a, expl, it["page"], {})
                if q:
                    pairsA.append((q, (a, expl, pg)))
        ckA, cfA, sA = selfcheck(pairsA)
        print(f"  A（按题号）：产出 {len(pairsA)} 题，可比对 {ckA}，矛盾 {cfA}"
              + ("  ✅" if cfA == 0 else "  ⚠️"))
        for stem, got, concl in sA:
            print(f"      ⚠️ 「{stem}」答案={got} 解析结论={concl}")

        # B 口径自洽
        order = [ans[k] for k in sorted(ans)]
        pairsB = []
        for i, q in enumerate(seq):
            if i >= len(order):
                break
            a, expl, pg = order[i]
            q2 = B.make_question(q.get("stem", ""), q.get("options") or [], a, expl, q.get("page"), {})
            if q2:
                pairsB.append((q2, (a, expl, pg)))
        ckB, cfB, sB = selfcheck(pairsB)
        print(f"  B（文档顺序）：产出 {len(pairsB)} 题，可比对 {ckB}，矛盾 {cfB}"
              + ("  ✅" if cfB == 0 else "  ⚠️"))
        for stem, got, concl in sB:
            print(f"      ⚠️ 「{stem}」答案={got} 解析结论={concl}")

        # 抽样对照：B 口径前 3 题与答案前 3 条是否对应
        print("  B 口径前 3 题抽样：")
        for q2, (a, expl, _pg) in pairsB[:3]:
            print(f"    - 题干「{q2['stem'][:46]}」")
            print(f"      答案 {q2['answer']}｜解析开头「{(expl or '')[:44]}」")
    return 0


if __name__ == "__main__":
    sys.exit(main())

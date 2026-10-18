#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""资料分析：学生版与答案版是否**共享同一套材料分组标题**？

若是，则可按「组号 + 组内题号」确定性对齐（不依赖数量容差、不依赖位置猜测），
这是可复核的对齐依据。实测两份文件的分组数量与每组小题数是否一致。
"""
import os
import re
import sys

WORK = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, WORK)
import build_bank as B  # noqa: E402

# 更宽的分组标题判据：一、二、… 后面接「根据/阅读/回答/材料」等
GRP_RE = re.compile(r"^\s*([一二三四五六七八九十]+)\s*[、.．]\s*(.{0,24})")


def groups(lines):
    out = []
    for i, (t, _p) in enumerate(lines):
        m = GRP_RE.match(t)
        if m:
            out.append((i, m.group(1), m.group(2).strip()))
    return out


def main():
    base = os.path.join(WORK, "text7")
    qp = os.path.join(base, "国家能源秋招常考易错1000题-资料分析-学生版.txt")
    ap = os.path.join(base, "国家能源秋招常考易错1000题-资料分析-答案版.txt")
    ql = B.expand_inline_options(B.clean_lines(open(qp, encoding="utf-8", errors="replace").read()))
    al = B.clean_lines(open(ap, encoding="utf-8", errors="replace").read())

    gq, ga = groups(ql), groups(al)
    print(f"学生版分组标题 {len(gq)} 个：")
    for i, cn, txt in gq[:12]:
        print(f"   行{i:5d} {cn}、{txt[:44]}")
    print(f"\n答案版分组标题 {len(ga)} 个：")
    for i, cn, txt in ga[:12]:
        print(f"   行{i:5d} {cn}、{txt[:44]}")

    # 每组小题数（学生版）
    print("\n学生版每组小题数：")
    qnums = B.question_starts(ql)
    bounds = [i for i, _c, _t in gq] + [len(ql)]
    for k in range(len(bounds) - 1):
        seg = ql[bounds[k]:bounds[k + 1]]
        d = B.parse_numbered_qfile(seg)
        print(f"   组{k+1}: {len(d)} 题（题号 {min(d) if d else '-'}~{max(d) if d else '-'}）")

    # 答案版每组答案数
    print("\n答案版每组答案数：")
    abounds = [i for i, _c, _t in ga] + [len(al)]
    tot = 0
    for k in range(len(abounds) - 1):
        seg = al[abounds[k]:abounds[k + 1]]
        d = B.parse_numbered_afile(seg)
        tot += len(d)
        print(f"   组{k+1}: {len(d)} 条（题号 {min(d) if d else '-'}~{max(d) if d else '-'}）")
    print(f"   合计 {tot} 条；全局解析得到 {len(B.parse_numbered_afile(al))} 条")
    return 0


if __name__ == "__main__":
    sys.exit(main())

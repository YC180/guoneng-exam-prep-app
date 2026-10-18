#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""资料分析分段解析出的 264 条里，有多少是**表格/统计行被误判为题干**？

判据（都指向“这不是一道题”）：
  - 选项数 < 2（真题必有多选支）；
  - 题干里没有中日韩汉字，且不含问号（纯数字/百分号/表格残留）。
只要过滤后条数落到答案文件的数量附近（250±容差），逐位对齐就成立。
"""
import os
import re
import sys

WORK = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, WORK)
import build_bank as B  # noqa: E402

CJK_RE = re.compile(r"[\u4e00-\u9fff]")


def main():
    base = os.path.join(WORK, "text7")
    for qf, af, label in (
        ("国家能源秋招常考易错1000题-资料分析-学生版.txt",
         "国家能源秋招常考易错1000题-资料分析-答案版.txt", "资料分析"),
        ("国家能源秋招常考易错1000题-数量关系-学生版.txt",
         "国家能源秋招常考易错1000题-数量关系-答案版.txt", "数量关系"),
    ):
        qp, ap = os.path.join(base, qf), os.path.join(base, af)
        qlines = B.expand_inline_options(
            B.clean_lines(open(qp, encoding="utf-8", errors="replace").read()))
        alines = B.clean_lines(open(ap, encoding="utf-8", errors="replace").read())
        items = []
        for seg in B.split_sections(qlines):
            d = B.parse_numbered_qfile(seg)
            for no in sorted(d):
                items.append(d[no])
        ans = B.parse_numbered_afile(alines)

        no_opt = [it for it in items if len(it["options"]) < 2]
        no_cjk = [it for it in items if not CJK_RE.search(it["stem"])]
        both = [it for it in items if len(it["options"]) < 2 and not CJK_RE.search(it["stem"])]
        keep = [it for it in items
                if len(it["options"]) >= 2 and (CJK_RE.search(it["stem"]) or "?" in it["stem"]
                                               or "？" in it["stem"])]
        print("=" * 72)
        print(f"【{label}】分段解析 {len(items)} 条；答案文件 {len(ans)} 条")
        print(f"  选项<2 的：{len(no_opt)} 条")
        print(f"  题干无汉字的：{len(no_cjk)} 条")
        print(f"  两者都占（必为表格残留）：{len(both)} 条")
        print(f"  过滤后保留：{len(keep)} 条  ← 与答案 {len(ans)} 相差 {abs(len(keep)-len(ans))}")
        print("  表格残留样例（选项<2 且无汉字）：")
        for it in both[:6]:
            print(f"    - 「{it['stem'][:58]}」选项 {len(it['options'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

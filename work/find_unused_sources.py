#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""发现“已提取文本但未接入题库”的题库类文件。

用问答密度（题号行数 / 答案标记数）估计文件是否含题目，
再与 build_bank 已接入的清单比对，列出未接入且题量可观的文件。
"""
import os
import re
import sys

WORK = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, WORK)
import build_bank as B  # noqa: E402

QNO = re.compile(r"^\s*\d{1,4}\s*[．.、]\s*\S", re.M)
ANS = re.compile(r"(【\s*答\s*案\s*】|答\s*[案家]\s*[:：]|参\s*考\s*答\s*案)", re.M)
OPT = re.compile(r"^\s*[A-D]\s*[．.、]\s*\S", re.M)


def known_paths():
    """已接入题库的源（规范化相对/绝对路径集合）。"""
    ks = set()
    for base, f, *_ in B.SOURCES:
        ks.add(os.path.normcase(os.path.join(WORK, base, f)))
    for f, _ch in B.SOURCES_T2:
        ks.add(os.path.normcase(os.path.join(B.TEXT2, f)))
    for qf, af, *_ in B.SOURCES_PAIR:
        ks.add(os.path.normcase(os.path.join(B.TEXT2, qf)))
    for f, _c, _h, _t in B.discover_ocr_sources():
        ks.add(os.path.normcase(os.path.join(B.OCR_DIR, f)))
    return ks


def main():
    ks = known_paths()
    rows = []
    for d in ("text", "text2", "text4", "text5", "text6", "text7", "ocr"):
        base = os.path.join(WORK, d)
        if not os.path.isdir(base):
            continue
        for dp, _dn, fns in os.walk(base):
            for fn in fns:
                if not fn.lower().endswith(".txt") or fn == "manifest.json":
                    continue
                fp = os.path.join(dp, fn)
                if os.path.getsize(fp) < 3000:
                    continue
                try:
                    t = open(fp, encoding="utf-8", errors="replace").read()
                except OSError:
                    continue
                nq = len(QNO.findall(t))
                na = len(ANS.findall(t))
                no = len(OPT.findall(t))
                if nq >= 15 and na >= 5 and no >= 20:
                    rows.append({"dir": d, "rel": os.path.relpath(fp, base), "qno": nq,
                                 "ans": na, "opt": no, "bytes": len(t),
                                 "used": os.path.normcase(fp) in ks})
    rows.sort(key=lambda r: (not r["used"], -r["qno"]))
    used = [r for r in rows if r["used"]]
    unused = [r for r in rows if not r["used"]]
    print(f"题库类文件共 {len(rows)} 个：已接入 {len(used)}，**未接入 {len(unused)}**\n")
    print("=== 未接入（按题号数降序，前 45）===")
    for r in unused[:45]:
        print(f"  qno={r['qno']:4d} ans={r['ans']:4d} opt={r['opt']:4d} {r['bytes']:8d}B  [{r['dir']}] {r['rel'][:88]}")
    tot = sum(r["qno"] for r in unused)
    print(f"\n未接入文件的题号行合计约 {tot} 行")
    return 0


if __name__ == "__main__":
    sys.exit(main())

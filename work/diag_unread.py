#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""诊断未被读取的 39 个文件：哪些在 OCR 队列里、哪些是真漏。"""
import json
import os
import sys

WORK = os.path.dirname(os.path.abspath(__file__))
ROOT = r"D:\DOWNLOADS\26国家能源集团通关资料"


def norm(p):
    return os.path.normcase(os.path.abspath(p)).rstrip("\\/")


def main():
    aud = json.load(open(os.path.join(WORK, "bank", "coverage_audit.json"), encoding="utf-8"))
    unread = [u["file"] for u in aud["unread"]]

    # OCR 候选（manifest 里已登记的）
    ocr_srcs = set()
    mp = os.path.join(WORK, "ocr", "manifest.json")
    if os.path.exists(mp):
        for rec in json.load(open(mp, encoding="utf-8")):
            ocr_srcs.add(norm(rec.get("src", "")))
    print(f"OCR manifest 已登记 {len(ocr_srcs)} 个源文件")

    # ocr.py 的候选全集：重新按同样规则算（扫描件候选）
    sys.path.insert(0, WORK)
    try:
        import ocr as O
        cands = O.collect(40.0)
        cand_norm = {norm(c["src"]) for c in cands}
        print(f"OCR 候选全集 {len(cand_norm)} 个")
    except Exception as exc:  # noqa: BLE001
        print(f"（无法重算 OCR 候选：{type(exc).__name__}: {exc}）")
        cand_norm = ocr_srcs

    will_ocr, real_miss = [], []
    for rel in unread:
        full = os.path.join(ROOT, rel)
        if norm(full) in cand_norm:
            will_ocr.append(rel)
        else:
            real_miss.append(rel)

    print(f"\n=== 在 OCR 队列中（会自动补上）：{len(will_ocr)} 个")
    for r in will_ocr:
        print("   ", r)
    print(f"\n=== ★ 真漏（OCR 也不会处理）：{len(real_miss)} 个")
    for r in real_miss:
        print("   ", r)

    # 7、与 9、是否重复
    d7 = os.path.join(ROOT, "7、【EPI通用能力练习题库】国家能源集团招聘")
    d9 = os.path.join(ROOT, "9、国家能源集团招聘EPI通用能力练习题库")
    def listing(d):
        out = []
        for dp, _dn, fns in os.walk(d):
            for fn in fns:
                out.append(os.path.relpath(os.path.join(dp, fn), d))
        return sorted(out)
    l7, l9 = listing(d7), listing(d9)
    print(f"\n=== 目录对比：7、={len(l7)} 文件，9、={len(l9)} 文件")
    only7 = [x for x in l7 if x not in l9]
    print(f"仅 7、有的文件：{len(only7)}")
    for x in only7[:25]:
        print("   ", x)
    return 0


if __name__ == "__main__":
    sys.exit(main())

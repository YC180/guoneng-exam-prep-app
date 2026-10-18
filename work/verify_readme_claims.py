#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""交付 README ↔ 产物对账（自维护）。

设计要点：**真值只从产物取**（题库 JSON、审计 JSON、目录、文件），
README 里的数字用正则从文本里**解析**出来，两边必须一致。
这样 README 一旦漂移就立刻报错，而且新增资料后无需人工同步期望值
（早期版本把期望值写死，结果新增 14 份资料后 12 项全部误报为“不一致”）。

另含自洽校验：状态分项之和 == 总量、覆盖度分档之和 == 资料总数。
"""
import json
import os
import re
import sys
from collections import Counter

APP = r"D:\DOWNLOADS\app"
WORK = r"D:\app project\work"


def main():
    readme = open(os.path.join(APP, "README.md"), encoding="utf-8").read()
    qs = json.load(open(os.path.join(WORK, "bank", "questions.json"), encoding="utf-8"))["questions"]
    cov = json.load(open(os.path.join(WORK, "bank", "read_coverage.json"), encoding="utf-8"))
    pack = json.load(open(os.path.join(WORK, "bank", "optional_pack.json"), encoding="utf-8"))
    qa = json.load(open(os.path.join(WORK, "bank", "quality_audit.json"), encoding="utf-8"))
    docs = sorted(os.listdir(os.path.join(APP, "docs")))
    js_mb = os.path.getsize(os.path.join(APP, "data", "questions.js")) / 1024 / 1024

    total = len(qs)
    st = Counter(q.get("answerStatus") for q in qs)
    cat = Counter(q.get("category") for q in qs)
    ocr = sum(1 for q in qs if "OCR" in (q.get("tags") or []))
    flagged = qa["flagged"]
    kinds = Counter(r["kind"] for r in cov)

    checks = []

    def claim(pattern, actual, label, group=1, cast=int, tol=0.051):
        """从 README 解析声明值，与真实值比对。tol 为浮点容差。"""
        m = re.search(pattern, readme)
        if not m:
            checks.append((False, label, "（README 未写）", actual))
            return
        got = cast(m.group(group))
        ok = abs(got - actual) < tol if cast is float else got == actual
        checks.append((ok, label, got, actual))

    # ---- 题库与答案状态 ----
    claim(r"- 题库：\*\*(\d+) 题\*\*", total, "题库总量")
    claim(r"已核对答案 (\d+) 题", st["verified"], "已核对")
    claim(r"待核对 (\d+) 题", st["needs_review"], "待核对")
    claim(r"无答案 (\d+) 题", st["missing"], "无答案")
    claim(r"\*\*(\d+) 题来自扫描件 OCR 识别\*\*", ocr, "OCR 题数")
    # ---- 类别构成 ----
    for name in ("时政", "EPI 通用能力", "历年真题", "模拟笔试", "企业文化"):
        key = "EPI通用能力" if name == "EPI 通用能力" else name
        claim(rf"{re.escape(name)} (\d+) 题", cat[key], f"类别 {name}")
    # ---- 结构质量（概览 + §八 两处都要对）----
    claim(r"结构完整：\*\*(\d+)/\d+", total - flagged, "结构完整题数")
    claim(r"结构完整：\*\*\d+/(\d+)", total, "结构完整分母")
    claim(r"题中 (\d+) 题结构完整", total - flagged, "§八 结构完整题数")
    claim(r"其余 (\d+) 题存在“不成形”问题", flagged, "结构问题题数")
    # ---- 覆盖度 ----
    claim(r"原资料共 \*\*(\d+) 份文件\*\*", len(cov), "资料总数")
    claim(r"：\*\*(\d+) 份\*\*可直接提取正文", kinds["OK-TEXT"], "OK-TEXT")
    claim(r"\*\*(\d+) 份\*\*文字层为空或残缺", kinds["OK-OCR"], "OK-OCR")
    claim(r"\*\*(\d+) 份\*\*为纯图片资源", kinds["IMAGE"], "IMAGE")
    claim(r"\*\*(\d+) 份\*\*仍无可用文本", kinds["EMPTY"], "EMPTY")
    claim(r"全部 \*\*(\d+) 份\*\*文件均已登记处理", len(cov), "来源 份数")
    # ---- 目录结构里的题量与体积 ----
    # README 写的是「约 N MB」，属取整表述 → 容差放到 0.6 MB
    claim(r"内置题库 window\.CE_BANK（约 (\d+) MB，\d+ 题）", js_mb, "questions.js 体积(MB)",
          cast=float, tol=0.6)
    claim(r"内置题库 window\.CE_BANK（约 \d+ MB，(\d+) 题）", total, "questions.js 题量")
    # ---- 报告与可选包 ----
    claim(r"(\d+) 份整理报告", len(docs), "docs 报告份数")
    claim(r"\*\*(\d+) 题\*\*，来自", pack["count"], "可选导入包题数")

    print("== README ↔ 产物 对账 ==")
    print(f"题库 {total}｜已核对 {st['verified']}｜待核对 {st['needs_review']}｜无答案 {st['missing']}"
          f"｜OCR 题 {ocr}｜结构问题 {flagged}｜资料 {len(cov)} 份｜docs {len(docs)} 份")
    print()
    fails = 0
    for ok, label, claimed, actual in checks:
        if ok:
            print(f"  ✅ {label}: {actual}")
        else:
            fails += 1
            print(f"  ❌ {label}: README 写 {claimed}，产物实际 {actual}")

    s1 = st["verified"] + st["needs_review"] + st["missing"]
    s2 = sum(kinds.values())
    assert s1 == total, f"状态分项合计 {s1} != 总量 {total}"
    assert s2 == len(cov), f"覆盖度分档合计 {s2} != 资料总数 {len(cov)}"
    print(f"\n自洽校验：状态分项 {s1} == 总量 {total} ✅；覆盖度分档 {s2} == 资料 {len(cov)} ✅")
    print(f"\n结果：{'README 与产物完全一致 ✅' if not fails else f'{fails} 项不一致 ❌'}")
    return 0 if not fails else 2


if __name__ == "__main__":
    sys.exit(main())

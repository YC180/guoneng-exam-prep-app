#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""生成 docs/06_题库校验报告.md —— 直接由 finalize 的真实产出派生。

为什么改成生成：此前这份报告是**手工誊抄**的副本，题量一旦重建就会过期
（实测已出现“11587/11294/63 题剔除/176 冲突”等旧数字，与当前题库不符）。
报告类文件一旦与数据脱钩就会误导使用者，因此改为**每次由校验结果生成**。
"""
import json
import os
import sys

WORK = os.path.dirname(os.path.abspath(__file__))
BANK = os.path.join(WORK, "bank")
APP_DOCS = r"D:\DOWNLOADS\app\docs"


def load(name):
    p = os.path.join(BANK, name)
    if not os.path.exists(p):
        return None
    return json.load(open(p, encoding="utf-8"))


def main():
    md_path = os.path.join(BANK, "validation_report.md")
    if not os.path.exists(md_path):
        print("缺少 work/bank/validation_report.md，请先运行 finalize_bank.py")
        return 1
    body = open(md_path, encoding="utf-8").read().strip()
    # 去掉 validation_report.md 自带的标题行，避免与本报告标题重复
    body_lines = body.split("\n")
    while body_lines and (not body_lines[0].strip() or body_lines[0].lstrip().startswith("# ")):
        body_lines.pop(0)
    body = "\n".join(body_lines).strip()
    rep = load("validation_report.json") or {}
    integ = load("integrity_audit.json") or {}

    L = []
    L.append("# 题库校验报告")
    L.append("")
    L.append("> **本报告由 `work/gen_validation_doc.py` 自动生成**，数据源为 `work/bank/validation_report.json`")
    L.append("> 与 `work/bank/integrity_audit.json`。题库每次重建后重跑即可，不会与题库脱钩。")
    L.append("> 生成时间：2026-10-18")
    L.append("")
    L.append("## 零、一页速览")
    L.append("")
    stats = rep.get("stats") or {}
    L.append(f"- 最终题目数：**{stats.get('total', '?')}**（原始解析 {rep.get('originalCount', '?')} 题，"
             f"去除完全重复 {rep.get('duplicatesRemoved', '?')} 题）")
    L.append(f"- 已核对：**{stats.get('status:verified', '?')}** 题（计入正确率统计）")
    L.append(f"- 待核对：**{stats.get('status:needs_review', '?')}** 题（**不计入**正确率统计）")
    L.append(f"- 无答案：**{stats.get('status:missing', '?')}** 题（**不计入**正确率统计）")
    hv = integ.get("hardVerified") or {}
    total_hard = sum(hv.values())
    if total_hard == 0:
        L.append("- **「已核对」的题中，答案键越界／选项键重复／题干为空等结构硬错误：0 条 ✅**")
        L.append("  （校验脚本 `work/integrity_audit.py`。这条为 0，「已核对」才名副其实，")
        L.append("   正确率才不是用坏数据算出来的。）")
    else:
        L.append(f"- ⚠️ **「已核对」的题中仍有 {total_hard} 条结构硬错误，必须修复**")
        for k, v in hv.items():
            if v:
                L.append(f"  - {k}：{v}")
    L.append("- 处置口径：凡**结构上无法作答**者一律降级为「待核对」或直接剔除，**绝不猜答案**。")
    L.append("")
    L.append("### 被剔除的题（无法作答，已不在题库中）")
    L.append("")
    ud = rep.get("unanswerableDropped") or {}
    L.append(f"共 **{ud.get('count', 0)}** 题：①选择题但选项不足 2 个（PDF 文字层把分式排版打散）；")
    L.append("②**没有任何选项、但答案是字母**（选项本体是图片：图形推理、资料分析图表题）。")
    L.append("")
    L.append("### 被降级的题（仍在题库中，但标为待核对、不进统计）")
    L.append("")
    cc = rep.get("answerCrossCheck") or {}
    L.append(f"- 答案与解析结论句冲突：**{cc.get('conflicts', 0)}** 题（原资料疑题号与答案错位）")
    ad = rep.get("answerabilityDowngraded") or {}
    L.append(f"- 结构不自洽（如选项键重复）：**{ad.get('count', 0)}** 题")
    for k, v in (ad.get("byReason") or {}).items():
        L.append(f"  - {k}：{v}")
    L.append("")
    L.append("---")
    L.append("")
    L.append(body)
    L.append("")
    L.append("---")
    L.append("")
    L.append("## 附：结构硬错误校验（`integrity_audit.py`）")
    L.append("")
    if integ:
        L.append("| 校验项 | 「已核对」题中的数量（必须为 0） | 已隔离（待核对）题中的数量 |")
        L.append("|---|---:|---:|")
        qz = integ.get("quarantined") or {}
        for k in ("题干为空", "选择题无选项", "选项键为空", "选项键重复", "答案键不在选项内"):
            L.append(f"| {k} | {hv.get(k, 0)} | {qz.get(k, 0)} |")
        L.append("")
        L.append("软问题（原资料客观缺失，不计入正确率）：")
        for k, v in (integ.get("soft") or {}).items():
            L.append(f"- {k}：{v}")
    else:
        L.append("（未生成 integrity_audit.json）")
    L.append("")

    os.makedirs(APP_DOCS, exist_ok=True)
    out = os.path.join(APP_DOCS, "06_题库校验报告.md")
    open(out, "w", encoding="utf-8").write("\n".join(L))
    print(f"写出 {out}（{len(L)} 行）")
    return 0


if __name__ == "__main__":
    sys.exit(main())

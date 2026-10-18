#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把「专业知识（近几年没考、按策略不入库）」里**确实可作答**的部分导出为可选导入包。

设计意图（与既定策略一致）：
  - 主题库**不并入**专业知识题（原资料标注「近几年没考」，用户明确要求维持降级）；
  - 但 OCR 既然读到了、且答案可核对，就不该白读 —— 因此导成一个**显式的可选包**，
    放在 APP 的 `可选导入/` 目录，使用者想练时自己导入，不导入也不影响题量与统计。

输出：
  D:\\DOWNLOADS\\app\\可选导入\\专业知识练习题_计算机类.csv
  D:\\DOWNLOADS\\app\\可选导入\\README.md

注意：APP 的 CSV 解析器是**逐行**切分（`text.split(/\\r?\\n/)`），带引号的字段若含换行会被拆错，
      因此这里把所有字段里的换行一律压成空格。
"""
import csv
import io
import json
import os
import re
import sys

WORK = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, WORK)
import build_bank as B  # noqa: E402

OUT_DIR = r"D:\DOWNLOADS\app\可选导入"
SRC = os.path.join(WORK, "ocr",
                   "4、【专业知识】国家能源集团专业知识（近几年没考，可选看）",
                   "计算机类", "2.计算机题库", "计算机类习题集.txt")
HEAD = ("id,type,stem,optionA,optionB,optionC,optionD,answer,"
        "explanation,category,chapter,tags,sourceFile")


def flat(s):
    """压掉换行与多余空白：APP 的 CSV 解析按行切分，字段内不能有换行。"""
    return re.sub(r"\s+", " ", (s or "")).strip()


# 非题目内容（OCR 元信息行、页标记、目录/章节标题页）——必须挡在题库之外，
# 否则会造出「题干是章节目录」的假题（实测本件首题题干曾是
#「# OCR: rapidocr dpi=200 第 1章：数据库等基础知识习题」）。
JUNK_STEM_RES = [
    re.compile(r"^#"),                                   # 元信息行
    re.compile(r"^\[\[PAGE"),                             # 页标记
    re.compile(r"^第\s*\d+\s*[章节]?\s*[:：]?.*习题\s*$"),   # 目录/章节标题
    re.compile(r"^[\d.\s]+$"),                            # 纯页码（如 “.2”“75”）
    # 题干里混进了**上一题的解析尾巴**（如「【解析】…所以队列是先 进先出的线性表。(6)设有…」）：
    # 这类题干实为两段内容拼接，已不是一个干净的单题，纳入只会误导 → 直接剔除。
    re.compile(r"【解析】"),
]


def is_junk(q):
    stem = flat(q.get("stem"))
    if len(re.sub(r"\s", "", stem)) < 8:
        return True
    for rx in JUNK_STEM_RES:
        if rx.search(stem):
            return True
    # 目录页特征：题干里没有任何问句/答题指令，却堆着章节名与页码
    if stem.count("第") >= 2 and stem.count("章") >= 2:
        return True
    return False


def main():
    if not os.path.exists(SRC):
        print("找不到源文本:", SRC)
        return 1
    raw = open(SRC, encoding="utf-8", errors="replace").read()
    # 先剥掉 `#` 开头的元信息行（# SOURCE / # OCR …），再清洗、再解析
    raw = re.sub(r"^#[^\n]*$", "", raw, flags=re.M)
    lines = B.ocr_lines(raw)
    exp = B.expand_inline_options(
        [(B.normalize_bare_option_letters(t), pg) for t, pg in lines])
    qs = B.parse_unnumbered(exp, {})

    keep = []
    dropped_junk = 0
    for q in qs:
        if q.get("answerStatus") != "verified":
            continue
        opts = q.get("options") or []
        keys = [str(o["key"]).upper() for o in opts]
        ans = [str(a).upper() for a in (q.get("answer") or [])]
        if len(opts) < 2 or not ans or any(a not in keys for a in ans):
            continue           # 结构不可作答的一律不要（与题库同一道门槛）
        if is_junk(q):
            dropped_junk += 1
            continue           # 章节目录/元信息等非题目内容
        keep.append(q)
    print(f"  过滤掉非题目内容 {dropped_junk} 条（目录/章节标题/元信息）")

    os.makedirs(OUT_DIR, exist_ok=True)
    csv_path = os.path.join(OUT_DIR, "专业知识练习题_计算机类.csv")
    buf = io.StringIO()
    # 注释行与表头**不能加引号**：APP 以「行首是否为 #」判断注释、以第一行为表头，
    # 若把 # 包进引号，行首变成 `"`，注释会被当成表头（实测报「CSV 缺少 stem 列」）。
    buf.write("# 可选导入包：计算机类专业练习题（**不属于**主题库）\n")
    buf.write("# 来源：26国家能源集团通关资料\\4、【专业知识】…\\计算机类\\2.计算机题库\\"
              "计算机类习题集.pdf（OCR）\n")
    buf.write("# 说明：主题库按备考策略不并入专业知识题；本包仅供需要时手动导入，"
              "导入前请自行确认答案\n")
    buf.write(HEAD + "\n")
    w = csv.writer(buf, quoting=csv.QUOTE_ALL, lineterminator="\n")
    for i, q in enumerate(keep, 1):
        o = {str(x["key"]).upper(): flat(x["text"]) for x in (q.get("options") or [])}
        w.writerow([
            f"zy-jsj-{i:04d}",
            q.get("type") or "single_choice",
            flat(q.get("stem")),
            o.get("A", ""), o.get("B", ""), o.get("C", ""), o.get("D", ""),
            "|".join(str(a) for a in q.get("answer") or []),
            flat(q.get("explanation")) or "",
            "专业知识（可选）",
            "计算机类习题集（OCR）",
            "专业知识|可选导入|OCR",
            "计算机类习题集.pdf",
        ])
    text = "\ufeff" + buf.getvalue()
    open(csv_path, "w", encoding="utf-8", newline="").write(text)
    print(f"写出 {csv_path}")
    print(f"  题数 {len(keep)}（源解析 {len(qs)} 题，仅取「已核对且结构可作答」者）")

    md = os.path.join(OUT_DIR, "README.md")
    open(md, "w", encoding="utf-8").write(
        "# 可选导入包（**不属于**主题库）\n\n"
        "这个目录里的文件**不被主题库计入**，APP 默认也不加载它们。\n\n"
        "## 为什么单独放这里\n\n"
        "`4、【专业知识】…` 下的资料（计算机、财会、通信）在原资料里就标注了\n"
        "「近几年没考，可选看」，因此按既定备考策略**只并入知识库备查、不计入题库题量**。\n"
        "但其中扫描件经 OCR 还原后，确实有一部分题**答案可核对、结构可作答**，\n"
        "白读可惜，于是导出成本包，供需要时手动导入。\n\n"
        f"## 文件\n\n"
        f"- `专业知识练习题_计算机类.csv`：**{len(keep)} 题**，来源 `计算机类习题集.pdf`（245 页扫描件，OCR 238,591 字）。\n"
        f"  筛选口径（全部可复核）：① 只取原资料答案**可核对**的题；② 选项不少于 2 个且答案键\n"
        f"  必须落在选项内；③ 剔除**非题目内容**（OCR 元信息行、页标记、章节目录页）与\n"
        f"  **题干混入上一题解析尾巴**（含「【解析】」字样）的残题 —— 本次共剔除 {dropped_junk} 条。\n"
        "- `（通信网优试题题库）`**未导出**：该件 OCR 后试解析 135 题，其中答案可核对的只有 **1 题**（采纳率 0.7%），\n"
        "  答案基本不可用，导出没有意义。\n\n"
        "## 怎么导入\n\n"
        "1. APP → 「资料与设置」→ 导入 → 选择本目录的 CSV；\n"
        "2. 导入后题目归入类别「专业知识（可选）」，与主题库统计**分开**统计不影响正确率；\n"
        "3. 导入前建议自行核对答案 —— 本包来自 OCR，虽已通过结构校验，仍可能有识别讹字。\n\n"
        "> 口径提醒：本包**不在** `README.md` 所述题库题量（11,521 题）之内，\n"
        "> 也不在 `docs/06_题库校验报告.md` 的校验范围内。\n")
    print(f"写出 {md}")
    json.dump({"count": len(keep), "source": os.path.relpath(SRC, WORK),
               "parsedTotal": len(qs), "csv": csv_path},
              open(os.path.join(WORK, "bank", "optional_pack.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())

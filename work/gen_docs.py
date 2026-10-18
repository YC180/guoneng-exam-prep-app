#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Generate the deliverable documentation from real data.

Outputs:
  D:\\DOWNLOADS\\app\\docs\\01_资料归纳总结.md

Everything is derived from the filesystem, the built question bank and the
extraction/OCR manifests — no hand-copied numbers.
"""
import json
import os
from collections import Counter, defaultdict

ROOT = r"D:\DOWNLOADS\26国家能源集团通关资料"
WORK = r"D:\app project\work"
OUTDIR = r"D:\DOWNLOADS\app\docs"

TEXT_ROOTS = ["text", "text2", "text3", "text4"]


def human(mb):
    return f"{mb:,.1f} MB" if mb >= 1 else f"{mb * 1024:,.0f} KB"


def walk_root():
    """Return {folder: {'files':n, 'mb':m, 'ext':Counter()}} for top-level dirs."""
    out = {}
    total_files = 0
    total_mb = 0.0
    ext_all = Counter()
    for entry in sorted(os.listdir(ROOT)):
        p = os.path.join(ROOT, entry)
        if not os.path.isdir(p):
            continue
        n = 0
        sz = 0
        ext = Counter()
        for dp, _d, fs in os.walk(p):
            for f in fs:
                fp = os.path.join(dp, f)
                try:
                    sz += os.path.getsize(fp)
                except OSError:
                    pass
                n += 1
                ext[os.path.splitext(f)[1].lower()] += 1
        out[entry] = {"files": n, "mb": sz / 1024 / 1024, "ext": ext}
        total_files += n
        total_mb += sz / 1024 / 1024
        ext_all.update(ext)
    return out, total_files, total_mb, ext_all


def load_manifests():
    """Collect extraction + OCR manifests."""
    rows = []
    for sub in TEXT_ROOTS:
        mp = os.path.join(WORK, sub, "manifest.json")
        if os.path.exists(mp):
            try:
                data = json.load(open(mp, encoding="utf-8"))
            except Exception:
                continue
            if isinstance(data, list):
                for r in data:
                    r["_stage"] = sub
                    rows.append(r)
    omp = os.path.join(WORK, "ocr", "manifest.json")
    ocr_rows = []
    if os.path.exists(omp):
        try:
            ocr_rows = json.load(open(omp, encoding="utf-8"))
        except Exception:
            ocr_rows = []
    return rows, ocr_rows


def text_stats():
    """Count produced .txt files and characters per extraction root."""
    out = {}
    for sub in TEXT_ROOTS + ["ocr"]:
        base = os.path.join(WORK, sub)
        if not os.path.isdir(base):
            continue
        n = 0
        chars = 0
        for dp, _d, fs in os.walk(base):
            for f in fs:
                if not f.lower().endswith(".txt"):
                    continue
                fp = os.path.join(dp, f)
                n += 1
                try:
                    chars += os.path.getsize(fp)
                except OSError:
                    pass
        out[sub] = {"files": n, "mb": chars / 1024 / 1024}
    return out


def bank_stats():
    p = os.path.join(WORK, "bank", "questions.json")
    if not os.path.exists(p):
        return None
    data = json.load(open(p, encoding="utf-8"))
    qs = data.get("questions") if isinstance(data, dict) else data
    if not isinstance(qs, list):
        return None
    cat = Counter()
    typ = Counter()
    st = Counter()
    chap = Counter()
    src = Counter()
    noexp = 0
    for q in qs:
        if not isinstance(q, dict):
            continue
        cat[q.get("category") or "未分类"] += 1
        typ[q.get("type") or "?"] += 1
        st[q.get("answerStatus") or "?"] += 1
        chap[q.get("chapter") or "未分类"] += 1
        src[q.get("sourceFile") or "未标注"] += 1
        if not (q.get("explanation") or "").strip():
            noexp += 1
    return {"total": len(qs), "cat": cat, "typ": typ, "st": st, "chap": chap,
            "src": src, "noexp": noexp, "generatedAt": data.get("generatedAt") if isinstance(data, dict) else None}


def validation():
    p = os.path.join(WORK, "bank", "validation_report.json")
    if not os.path.exists(p):
        return None
    v = json.load(open(p, encoding="utf-8"))
    # 该文件把异常明细放在 issues（[{id, issue}]），按 issue 计数
    if isinstance(v, dict) and "byIssue" not in v:
        cnt = Counter()
        for it in v.get("issues", []):
            if isinstance(it, dict):
                cnt[it.get("issue") or "未知"] += 1
        v["byIssue"] = dict(cnt)
    return v


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    folders, total_files, total_mb, ext_all = walk_root()
    tstats = text_stats()
    man, ocr_man = load_manifests()
    bs = bank_stats()
    val = validation()

    L = []
    A = L.append
    A("# 资料归纳总结")
    A("")
    A("国家能源集团招聘笔试备考资料 —— 全量盘点、提取与题库化结果")
    A("")
    A(f"- 生成时间：{__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}")
    A(f"- 资料根目录：`{ROOT}`")
    A(f"- 文件总数：**{total_files}** 个，合计 **{human(total_mb)}**")
    A(f"- 顶层目录：**{len(folders)}** 个")
    A("")

    A("## 一、资料总览（按顶层目录）")
    A("")
    A("| 目录 | 文件数 | 体积 | 主要格式 | 处理结果 |")
    A("|---|---:|---:|---|---|")
    note = {
        "1、2025国家能源集团招聘考试知识点讲义和企业文化": "已提取（讲义、企业文化试题、官方文化手册）",
        "2、【行测知识】国家能源行测部分解题技巧方法汇总": "已提取（解题技巧讲义）",
        "3、【行测知识】国家能源行测部分分题型刷题提分题库": "**原为扫描件，已 OCR 提取**",
        "4、【专业知识】国家能源集团专业知识（近几年没考，可选看）": "已 OCR 提取；按“近几年没考”**未纳入题库**",
        "5、【模拟试题】国家能源招聘笔试模拟试题": "已提取",
        "6、【国家能源集团招聘】12-25年笔试真题": "已提取 + 扫描年份已 OCR",
        "7、国家能源集团招聘考试辅导资料（赠送）": "与 9、 目录内容重复，未重复处理",
        "8、时政【全年持续更新】": "已提取 + 扫描件已 OCR",
        "9、国家能源集团招聘EPI通用能力练习题库": "已提取（主力题库来源）",
        "10、国家能源集团概况、业务体系": "已提取",
        "11、面试学习资料包": "已提取 + 大部已 OCR",
    }
    for name in sorted(folders, key=lambda x: (len(x.split("、")[0]), x)):
        f = folders[name]
        exts = "、".join(f"{k or '无扩展名'}×{v}" for k, v in f["ext"].most_common(3))
        A(f"| {name} | {f['files']} | {human(f['mb'])} | {exts} | {note.get(name, '已处理')} |")
    A(f"| **合计** | **{total_files}** | **{human(total_mb)}** | "
      + "、".join(f"{k}×{v}" for k, v in ext_all.most_common(6)) + " | — |")
    A("")

    A("## 二、文本提取成果")
    A("")
    A("| 阶段 | 输出 txt | 体积 | 说明 |")
    A("|---|---:|---:|---|")
    stage_note = {
        "text": "讲义、企业文化试题、解题技巧、模拟卷、2012—2025 真题、EPI 题库、概况业务体系",
        "text2": "时政（2024—2026 各月）、面试文本",
        "text3": "面试（Word 二进制 .doc 经 Word COM 转文本）",
        "text4": "面试、专业知识、官方《企业文化核心理念》手册（62 页，含文字层）",
        "ocr": "扫描件 OCR 成果（图片型 PDF → 中文文本）",
    }
    for k in ["text", "text2", "text3", "text4", "ocr"]:
        if k in tstats:
            t = tstats[k]
            A(f"| `work\\{k}` | {t['files']} | {human(t['mb'])} | {stage_note.get(k, '')} |")
    A("")

    if man or ocr_man:
        A("### 提取清单统计")
        A("")
        ok = sum(1 for r in man if r.get("status") == "ok")
        err = sum(1 for r in man if r.get("status") == "error")
        skip = sum(1 for r in man if str(r.get("status", "")).startswith("skip"))
        A(f"- 常规提取记录：{len(man)} 条（成功 {ok}，失败 {err}，跳过 {skip}）")
        if ocr_man:
            ook = sum(1 for r in ocr_man if r.get("status") == "ok")
            oerr = sum(1 for r in ocr_man if r.get("status") == "error")
            A(f"- OCR 记录：{len(ocr_man)} 条（成功 {ook}，失败 {oerr}）")
        A("")

    if bs:
        A("## 三、题库构成")
        A("")
        A(f"- 入库总量：**{bs['total']}** 题")
        A(f"- 无解析题目：{bs['noexp']} 题（原资料未提供解析，APP 如实标注，不自动补写）")
        A("")
        A("### 按资料类别")
        A("")
        A("| 类别 | 题量 |")
        A("|---|---:|")
        for k, v in bs["cat"].most_common():
            A(f"| {k} | {v} |")
        A("")
        A("### 按题型")
        A("")
        tlab = {"single_choice": "单选题", "multiple_choice": "多选题",
                "true_false": "判断题", "fill_blank": "填空题", "short_answer": "简答题"}
        A("| 题型 | 题量 |")
        A("|---|---:|")
        for k, v in bs["typ"].most_common():
            A(f"| {tlab.get(k, k)} | {v} |")
        A("")
        A("### 按答案状态")
        A("")
        slab = {"verified": "已核对（计入正确率统计）",
                "needs_review": "待核对（**不计入**统计）",
                "missing": "无答案（**不计入**统计）"}
        A("| 状态 | 题量 |")
        A("|---|---:|")
        for k, v in bs["st"].most_common():
            A(f"| {slab.get(k, k)} | {v} |")
        A("")
        A("### 题量最多的 15 个章节")
        A("")
        A("| 章节 | 题量 |")
        A("|---|---:|")
        for k, v in bs["chap"].most_common(15):
            A(f"| {k} | {v} |")
        A("")

    if val:
        A("## 四、题库校验结果")
        A("")
        A(f"- 校验题目总数：{val.get('total', '—')}")
        A(f"- 重复 ID：{len(val.get('duplicateIds', []))}")
        A(f"- 异常条目：{val.get('issueCount', '—')}")
        A("")
        A("| 异常类型 | 数量 | 是否为错误 |")
        A("|---|---:|---|")
        kinds = val.get("byIssue", {})
        for k, v in sorted(kinds.items(), key=lambda x: -x[1]):
            iserr = "否（原资料客观缺失）" if ("解析缺失" in k or "待核对" in k or "无答案" in k) else "需关注"
            A(f"| {k} | {v} | {iserr} |")
        A("")
        A("完整明细见 APP 内「资料与设置 → 导出题库校验报告」，或 `work\\bank\\validation_report.md`。")
        A("")

    A("## 五、扫描件与 OCR")
    A("")
    if ocr_man:
        okc = [r for r in ocr_man if r.get("status") == "ok"]
        errc = [r for r in ocr_man if r.get("status") == "error"]
        pages = sum(r.get("pages", 0) for r in okc)
        chars = sum(r.get("chars", 0) for r in okc)
        A(f"- 已 OCR 成功 **{len(okc)}** 个文件，共 **{pages}** 页，产出 **{chars:,}** 字符")
        if errc:
            A(f"- OCR 失败 {len(errc)} 个：")
            for r in errc[:20]:
                A(f"  - `{r.get('rel', r.get('src'))}`：{r.get('error', '')}")
        A("")
        A("### OCR 明细（按分级）")
        A("")
        A("| 分级 | 文件 | 页数 | 字符 |")
        A("|---|---:|---:|---:|")
        bytier = defaultdict(lambda: [0, 0, 0])
        for r in okc:
            t = r.get("tier", 9)
            bytier[t][0] += 1
            bytier[t][1] += r.get("pages", 0)
            bytier[t][2] += r.get("chars", 0)
        tname = {1: "1 行测分题型题库", 2: "2 历年真题/模拟卷", 3: "3 时政",
                 4: "4 讲义", 5: "5 集团概况", 6: "6 面试", 7: "7 专业知识", 9: "9 其他"}
        for t in sorted(bytier):
            n, pg, ch = bytier[t]
            A(f"| {tname.get(t, t)} | {n} | {pg} | {ch:,} |")
        A("")
        pend = [r for r in ocr_man if r.get("status") == "pending"]
        if pend:
            A(f"- 尚在处理中：{len(pend)} 个")
            A("")
    else:
        A("OCR 结果清单尚未生成（任务进行中）。")
        A("")

    A("### OCR 内容的入库约定")
    A("")
    A("- 每题都带标签 `OCR`；答案无法对应到选项的一律标为 `待核对`，不计入正确率统计。")
    A("- 解析被 OCR 讹字严重污染的题目，解析替换为“（OCR 识别不可靠，本段解析未采用；请查阅原资料对应页）”并打标签 `解析待核`。")
    A("- **图形推理 350 题不入库**：OCR 后选项全为“如上图所示”，图形无法提取，题目不含可作答信息。")
    A("- 资料分析（图表）类已打标签 `缺图表`、`材料需回原文`：题干完整但原统计表格未随文本保留。")
    A("- OCR 为尽力而为：`work\\ocr\\manifest.json` 中逐文件记录页数、字符数、空页数，可核查。")
    A("")

    A("## 六、分科目归纳报告")
    A("")
    docs = [
        ("03_时政考点归纳.md", "时政考点归纳", "2026 年 1—4 月核心考点、问→答 65 条、缺失与存疑清单"),
        ("04_行测EPI考点归纳.md", "行测 / EPI 考点归纳", "五大题型解题方法、原文例题、题库题量实测、提分优先级"),
        ("05_面试与专业知识归纳.md", "面试与专业知识归纳", "面试形式与题型、专业知识范围、问→答要点"),
        ("02_老旧信息联网核实报告.md", "老旧信息联网核实报告", "过时信息逐条对照与官网核实结果"),
    ]
    A("| 报告 | 内容 |")
    A("|---|---|")
    for fn, title, desc in docs:
        A(f"| [{title}]({fn}) | {desc} |")
    A("")

    A("## 七、处理原则（重要）")
    A("")
    A("1. **不编造**：原资料没有的答案、解析、题目，一律不补写、不推测。")
    A("2. **可回溯**：每题都带 `sourceFile`（必要时含页码），可在原资料中核对。")
    A("3. **不糊弄错误**：题库校验报告如实记录所有异常条目，不静默吞掉。")
    A("4. **区分可信度**：`已核对` / `待核对` / `无答案` 三态，只有前者计入正确率统计。")
    A("5. **时效信息以官网为准**：本地资料多为 2022—2025 年版本，凡与官网冲突处以官网为准，并保留旧值供对照（见核实报告）。")
    A("6. **演示数据与正式题库分离**：内置题库全部来自真实资料；用户导入的题目单独存储，不混写。")
    A("")

    out = os.path.join(OUTDIR, "01_资料归纳总结.md")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")
    print(f"写出 {out}（{len(L)} 行）")


if __name__ == "__main__":
    main()

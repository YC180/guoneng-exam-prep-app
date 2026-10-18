#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Finalise the question bank: dedup, validate, and emit browser-loadable assets.

Outputs (into work/bank and the app data dir):
  questions.json            standard schema (spec section 6)
  validation_report.json    machine-readable audit
  validation_report.md      human-readable audit
  app/data/questions.js     window.CE_BANK = {...}  (loads from file:// too)
"""
import json
import os
import re
import sys
import unicodedata
from collections import Counter, defaultdict

WORK = r"D:\app project\work"
BANK = os.path.join(WORK, "bank")
APP = r"D:\DOWNLOADS\app"

TYPE_LABEL = {
    "single_choice": "单选题", "multiple_choice": "多选题", "true_false": "判断题",
    "fill_blank": "填空题", "short_answer": "简答题",
}


def norm_stem(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "")
    s = re.sub(r"[\s\u3000]+", "", s)
    s = re.sub(r"[，。、；：？！,.;:?!\"'“”‘’（）()【】\[\]…—\-_]+", "", s)
    return s


# ---------------------------------------------------------------- 答案自洽复核
# 许多资料的解析里带独立的结论句（“因此，选择D选项”）。若它与解析出的 answer
# 不一致，极可能是题号与答案错位——此时**不能猜**，只能降级为待核对，
# 使其不进入正确率统计。
CONCL_RES = [
    re.compile(r"选择\s*([A-Ha-h])\s*选项"),
    re.compile(r"故选\s*([A-Ha-h])"),
    re.compile(r"故本题\s*选\s*([A-Ha-h])"),
    re.compile(r"本题\s*选\s*([A-Ha-h])"),
    re.compile(r"应选\s*([A-Ha-h])"),
    re.compile(r"正确答案\s*(?:为|是)?\s*([A-Ha-h])"),
    re.compile(r"选\s*([A-Ha-h])\s*项"),
    re.compile(r"答案\s*(?:为|是)\s*([A-Ha-h])\b"),
    re.compile(r"【\s*答\s*案\s*】\s*([A-Ha-h])"),
]


def cross_check_answers(questions):
    """返回 (一致数, 冲突明细列表)，并把冲突题降级为 needs_review。"""
    ok = 0
    conflicts = []
    for q in questions:
        ans = [str(a).upper() for a in (q.get("answer") or [])]
        expl = q.get("explanation") or ""
        letters = []
        for rx in CONCL_RES:
            letters += [m.group(1).upper() for m in rx.finditer(expl)]
        uniq = sorted(set(letters))
        if len(uniq) != 1 or not ans:
            continue
        if ans == uniq:
            ok += 1
            continue
        conflicts.append({
            "id": q["id"], "sourceFile": q.get("sourceFile"), "sourcePage": q.get("sourcePage"),
            "chapter": q.get("chapter"), "stem": (q.get("stem") or "")[:90],
            "answer": ans, "explanationSays": uniq, "before": q.get("answerStatus"),
        })
        q["answerStatus"] = "needs_review"
        q["tags"] = list(dict.fromkeys(list(q.get("tags") or []) + ["答案与解析不一致"]))
        q["reviewNote"] = (f"解析结论句指向 {'/'.join(uniq)}，与答案字段 {'/'.join(ans)} 不一致，"
                           f"疑为题号与答案错位，已标为待核对、不计入正确率。")
    return ok, conflicts


def drop_unanswerable(questions):
    """剔除“结构上无法作答”的题：这类题留着只会污染练习。

    两类成因：
      1) 选择题但选项不足 2 个 —— 原 PDF 文字层的分式/图片排版被打散；
      2) **没有任何选项、但答案是字母** —— 选项本体是图片（图形推理、
         资料分析图表题），PDF 里取不到选项文字，用户根本看不到可选项。
    剔除后记录来源，便于在报告中说明。
    """
    kept, dropped = [], []
    for q in questions:
        opts = q.get("options") or []
        ans = [str(a).strip().upper() for a in (q.get("answer") or []) if str(a).strip()]
        reason = None
        if q.get("type") in ("single_choice", "multiple_choice") and len(opts) < 2:
            reason = f"选择题但选项不足 2 个（{len(opts)}）"
        elif not opts and ans and all(re.fullmatch(r"[A-H]", a) for a in ans):
            reason = "无任何选项但答案为字母（选项本体是图片，无法作答题）"
        if reason:
            dropped.append({"id": q["id"], "sourceFile": q.get("sourceFile"),
                            "options": len(opts), "reason": reason,
                            "stem": (q.get("stem") or "")[:80]})
            continue
        kept.append(q)
    return kept, dropped


def enforce_answerability(questions):
    """保证 `answerStatus=verified` 名副其实：结构上不自洽的题一律降级为待核对。

    为什么必须做：标为 verified 的题会进入正确率统计。若某题「答案键不在选项里」
    或「选项键重复」（通常是两道题被并成了一题），它在结构上根本无法作答，
    却仍参与统计 —— 等于用坏数据算掌握率。
    这里**只降级、不改答案**：不确定就标待核对，绝不猜哪个选项对。
    """
    downgraded = []
    for q in questions:
        if q.get("answerStatus") != "verified":
            continue
        keys = [str(o.get("key") or "").strip().upper() for o in (q.get("options") or [])]
        kset = {k for k in keys if k}
        ans = [str(a).strip().upper() for a in (q.get("answer") or []) if str(a).strip()]
        reason = None
        if not ans:
            q["answerStatus"] = "missing"
            continue
        is_choice = q.get("type") in ("single_choice", "multiple_choice")
        letter_ans = [a for a in ans if re.fullmatch(r"[A-H]", a)]
        if is_choice and any(a not in kset for a in ans):
            reason = (f"答案 {'/'.join(ans)} 不在选项键 "
                      f"{'/'.join(sorted(kset)) if kset else '（无选项）'} 内")
        elif not is_choice and letter_ans and any(a not in kset for a in letter_ans):
            # 判断题/填空题本可以用“正确/错误”或文字作答（无选项是正常的），
            # 但若它拿字母当答案、选项里又没有这个字母，说明选项本体是图片。
            reason = f"答案 {'/'.join(letter_ans)} 为字母但选项中无此键（选项应为图片）"
        elif any(n > 1 for n in Counter(k for k in keys if k).values()):
            reason = "选项键重复（疑两道题被合并为一题）"
        elif is_choice and len(keys) < 2:
            reason = f"选择题但选项不足 2 个（{len(keys)}）"
        elif q.get("type") == "single_choice" and len(ans) > 1:
            reason = f"单选题却有多个答案（{'/'.join(ans)}）"
        if reason:
            downgraded.append({"id": q["id"], "sourceFile": q.get("sourceFile"),
                               "chapter": q.get("chapter"), "reason": reason,
                               "stem": (q.get("stem") or "")[:80]})
            q["answerStatus"] = "needs_review"
            q["tags"] = list(dict.fromkeys(list(q.get("tags") or []) + ["结构不自洽"]))
            q["reviewNote"] = reason + "；该题结构上无法作答，已标为待核对、不计入正确率。"
    return downgraded


def validate(questions):
    issues = []
    dup_ids = [k for k, v in Counter(q["id"] for q in questions).items() if v > 1]
    seen_stem = {}
    dups = 0
    for q in questions:
        key = norm_stem(q["stem"]) + "|" + "".join(sorted(q.get("answer") or []))
        if key in seen_stem:
            dups += 1
            q["_dupOf"] = seen_stem[key]
        else:
            seen_stem[key] = q["id"]

    stats = Counter()
    chapter = defaultdict(lambda: Counter())
    for q in questions:
        t = q.get("type")
        stats["total"] += 1
        stats[f"type:{t}"] += 1
        status = q.get("answerStatus") or "missing"
        stats[f"status:{status}"] += 1
        ch = q.get("chapter") or "未分类"
        chapter[q.get("category", "未分类")][ch] += 1
        if not (q.get("stem") or "").strip():
            issues.append({"id": q["id"], "issue": "题干为空"})
        if t in ("single_choice", "multiple_choice"):
            opts = q.get("options") or []
            if len(opts) < 2:
                issues.append({"id": q["id"], "issue": f"选项数不足({len(opts)})"})
            keys = {o.get("key") for o in opts}
            ans = q.get("answer") or []
            if not ans:
                issues.append({"id": q["id"], "issue": "无答案"})
            for a in ans:
                if a not in keys:
                    issues.append({"id": q["id"], "issue": f"答案{a}不在选项中"})
            if any(not (o.get("text") or "").strip() for o in opts):
                issues.append({"id": q["id"], "issue": "存在空选项文本"})
        if t == "single_choice" and len(q.get("answer") or []) > 1:
            issues.append({"id": q["id"], "issue": "单选却有多答案"})
        if t == "multiple_choice" and len(q.get("answer") or []) < 2:
            issues.append({"id": q["id"], "issue": "多选却只有1个答案"})
        if not (q.get("explanation") or "").strip():
            issues.append({"id": q["id"], "issue": "解析缺失（非错误）"})
        if not q.get("sourceFile"):
            issues.append({"id": q["id"], "issue": "来源缺失"})
        if q.get("answerStatus") == "needs_review":
            issues.append({"id": q["id"], "issue": "答案待核对"})
    return {
        "duplicateIds": dup_ids, "duplicateQuestions": dups,
        "issueCount": len(issues), "issues": issues[:4000],
        "stats": dict(stats),
        "chapters": {c: dict(v) for c, v in chapter.items()},
    }


def main():
    src = os.path.join(BANK, "questions.json")
    bank = json.load(open(src, encoding="utf-8"))
    qs = bank["questions"]
    # drop exact duplicates (same normalised stem + same answer)
    seen = {}
    kept = []
    for q in qs:
        key = norm_stem(q["stem"]) + "|" + "".join(sorted(q.get("answer") or []))
        if key in seen:
            continue
        seen[key] = q["id"]
        kept.append(q)
    removed = len(qs) - len(kept)
    # 剔除无法作答的残题（选择题但选项 < 2）
    kept, dropped = drop_unanswerable(kept)
    # 答案自洽复核：与解析结论句冲突的题目降级为待核对（不猜答案）
    cc_ok, conflicts = cross_check_answers(kept)
    # 结构自洽复核：自称“已核对”但结构上无法作答的题，一律降级为待核对
    downgraded = enforce_answerability(kept)
    # renumber ids for stability
    for i, q in enumerate(kept, 1):
        q["id"] = f"q{i:05d}"
    bank["questions"] = kept
    bank["count"] = len(kept)

    report = validate(kept)
    report["duplicatesRemoved"] = removed
    report["originalCount"] = len(qs)
    report["unanswerableDropped"] = {
        "count": len(dropped),
        "bySource": {k: v for k, v in
                     sorted(Counter(d["sourceFile"] for d in dropped).items(),
                            key=lambda x: -x[1])},
        "samples": dropped[:40],
    }
    report["answerCrossCheck"] = {
        "corroborated": cc_ok + len(conflicts),
        "consistent": cc_ok,
        "conflicts": len(conflicts),
        "rate": round(cc_ok / (cc_ok + len(conflicts)), 4) if (cc_ok + len(conflicts)) else None,
        "conflictDetails": conflicts,
    }
    report["answerabilityDowngraded"] = {
        "count": len(downgraded),
        "byReason": {k: v for k, v in
                     sorted(Counter(d["reason"] for d in downgraded).items(),
                            key=lambda x: -x[1])},
        "bySource": {k: v for k, v in
                     sorted(Counter(d["sourceFile"] for d in downgraded).items(),
                            key=lambda x: -x[1])},
        "samples": downgraded[:40],
    }

    json.dump(bank, open(os.path.join(BANK, "questions.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    json.dump(report, open(os.path.join(BANK, "validation_report.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    lines = ["# 题库校验报告", "",
             f"- 原始解析题目数：{len(qs)}",
             f"- 去除完全重复题：{removed}",
             f"- 剔除无法作答的残题（选择题但选项不足 2 个）：**{len(dropped)}**",
             f"- 最终题目数：**{len(kept)}**", ""]
    lines.append("## 按题型")
    for k, v in sorted(report["stats"].items()):
        if k.startswith("type:"):
            lines.append(f"- {TYPE_LABEL.get(k[5:], k[5:])}：{v}")
    lines.append("")
    lines.append("## 按答案状态")
    for k, v in sorted(report["stats"].items()):
        if k.startswith("status:"):
            label = {"verified": "已核对", "needs_review": "待核对", "missing": "无答案"}.get(k[7:], k[7:])
            lines.append(f"- {label}：{v}")
    lines.append("")
    ud = report["unanswerableDropped"]
    lines.append("## 已剔除的无法作答残题")
    lines.append("")
    lines.append(f"- 数量：**{ud['count']}** 题（结构上无法作答，已从题库移除）")
    lines.append("- 两类成因：①选择题但选项不足 2 个（原 PDF 文字层把分式/图片排版打散）；")
    lines.append("  ②**没有任何选项但答案是字母**（选项本体是图片：图形推理、资料分析图表题）。")
    lines.append("")
    if ud["bySource"]:
        lines.append("| 来源 | 剔除数 |")
        lines.append("|---|---:|")
        for s, n in list(ud["bySource"].items())[:15]:
            lines.append(f"| `{os.path.basename(s or '')}` | {n} |")
        lines.append("")
    cc = report["answerCrossCheck"]
    lines.append("## 答案自洽复核（解析结论句 ↔ 答案字段）")
    lines.append("")
    lines.append(f"- 有独立佐证的题目：{cc['corroborated']} 题")
    lines.append(f"- 两者一致：{cc['consistent']} 题"
                 + (f"（一致率 {cc['rate']*100:.2f}%）" if cc["rate"] is not None else ""))
    lines.append(f"- **两者冲突（已降级为待核对）：{cc['conflicts']} 题**")
    lines.append("")
    lines.append("> 说明：解析里的结论句是独立于答案字段的第二处答案信息。两者冲突通常意味着")
    lines.append("> 原资料的**题号与答案错位**，此时不猜测哪个对，一律标为“待核对”，不计入正确率。")
    lines.append("")
    ad = report["answerabilityDowngraded"]
    lines.append("## 结构自洽复核（“已核对”是否名副其实）")
    lines.append("")
    lines.append(f"- **降级为待核对：{ad['count']} 题**（原本标着“已核对”，但结构上根本无法作答）")
    lines.append("- 触发原因分布：")
    for k, v in ad["byReason"].items():
        lines.append(f"  - {k}：{v} 题")
    lines.append("")
    lines.append("> 为什么必须降级：标为“已核对”的题会进入正确率统计。若答案键不在选项里、")
    lines.append("> 或选项键重复（两道题被并成一题），该题根本没法作答，却仍参与统计 ——")
    lines.append("> 等于用坏数据算掌握率。此处**只降级、不改答案**，不确定就标待核对。")
    lines.append("")
    if ad["bySource"]:
        lines.append("| 来源 | 降级数 |")
        lines.append("|---|---:|")
        for s, n in list(ad["bySource"].items())[:12]:
            lines.append(f"| `{os.path.basename(s or '')}` | {n} |")
        lines.append("")
    if conflicts:
        lines.append("### 冲突题明细")
        lines.append("")
        lines.append("| 题号 | 来源 | 页码 | 答案字段 | 解析结论 | 题干 |")
        lines.append("|---|---|---|---|---|---|")
        for c in conflicts[:200]:
            stem = (c["stem"] or "").replace("|", "\\|").replace("\n", " ")
            lines.append(f"| `{c['id']}` | {os.path.basename(c['sourceFile'] or '')[:40]} | "
                         f"{c['sourcePage']} | {'/'.join(c['answer'])} | "
                         f"{'/'.join(c['explanationSays'])} | {stem} |")
        lines.append("")
    lines.append("## 按类别/章节")
    for cat, chs in sorted(report["chapters"].items()):
        total = sum(chs.values())
        lines.append(f"### {cat}（{total} 题）")
        for ch, n in sorted(chs.items(), key=lambda x: -x[1]):
            lines.append(f"- {ch}：{n}")
    lines.append("")
    lines.append(f"## 异常明细（共 {report['issueCount']} 条，下列为已记录明细）")
    for it in report["issues"][:400]:
        lines.append(f"- `{it['id']}` {it['issue']}")
    open(os.path.join(BANK, "validation_report.md"), "w", encoding="utf-8").write("\n".join(lines))

    # browser asset
    os.makedirs(os.path.join(APP, "data"), exist_ok=True)
    payload = json.dumps(bank, ensure_ascii=False, separators=(",", ":"))
    with open(os.path.join(APP, "data", "questions.js"), "w", encoding="utf-8") as fh:
        fh.write("/* 国家能源集团备考题库 —— 自动生成，请勿手工编辑 */\n")
        fh.write("window.CE_BANK = ")
        fh.write(payload)
        fh.write(";\n")
    size_mb = os.path.getsize(os.path.join(APP, "data", "questions.js")) / 1024 / 1024
    print(f"final={len(kept)} removed={removed} issues={report['issueCount']}")
    print(f"剔除无法作答残题：{len(dropped)} 题")
    print(f"stats={report['stats']}")
    print(f"答案自洽复核：有独立佐证 {cc['corroborated']} 题，一致 {cc['consistent']}，"
          f"冲突降级 {cc['conflicts']}"
          + (f"（一致率 {cc['rate']*100:.2f}%）" if cc["rate"] is not None else ""))
    print(f"结构自洽复核：降级为待核对 {len(downgraded)} 题")
    for k, v in ad["byReason"].items():
        print(f"    {k}: {v}")
    print(f"app bank size = {size_mb:.2f} MB")


if __name__ == "__main__":
    sys.exit(main())

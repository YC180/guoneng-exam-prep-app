#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""题库内部一致性审计：答案键、选项键、题型与答案数量的自洽性。

这是“标准化题库”的核心校验：一道标准选择题必须满足
  - 题干非空
  - 选项键唯一且非空
  - 答案键**全部落在选项键集合内**（越界即错题）
  - 题型与答案个数自洽（单选=1，多选≥2）
  - 判断题/填空题不强求选项

输出 work/bank/integrity_audit.json，并在有“越界答案”等硬错误时非零退出。
"""
import json
import os
import re
import sys
from collections import Counter, defaultdict

WORK = os.path.dirname(os.path.abspath(__file__))
BANK = os.path.join(WORK, "bank")


def main():
    qs = json.load(open(os.path.join(BANK, "questions.json"), encoding="utf-8"))["questions"]
    hard = defaultdict(list)          # 仍然“已核对”却结构不自洽：必须为 0，否则污染正确率
    quarantined = defaultdict(list)   # 已降级为待核对的结构缺陷：预期存在，如实统计
    soft = defaultdict(list)          # 原资料客观缺失，不计入正确率

    def put(bucket, key, item):
        bucket[key].append(item)

    for q in qs:
        qid = q.get("id")
        stem = (q.get("stem") or "").strip()
        opts = q.get("options") or []
        keys = [str(o.get("key") or "").strip() for o in opts]
        ans = [str(a).strip().upper() for a in (q.get("answer") or []) if str(a).strip()]
        typ = q.get("type")
        verified = q.get("answerStatus") == "verified"

        def flag(key, item=None):
            put(hard if verified else quarantined, key, item if item is not None else qid)

        if not stem:
            flag("题干为空")
        is_choice = typ in ("single_choice", "multiple_choice")
        if not opts and is_choice:
            flag("选择题无选项")
        if keys and any(not k for k in keys):
            flag("选项键为空")
        dup = [k for k, n in Counter(keys).items() if n > 1 and k]
        if dup:
            flag("选项键重复", (qid, dup))
        kset = {k.upper() for k in keys if k}
        # 判断题/填空题允许用“正确/错误”或文字作答（无选项是正常的），
        # 只对“拿字母当答案却没这个选项”的情况判错。
        for a in ans:
            if (is_choice and a not in kset) or \
               (not is_choice and re.fullmatch(r"[A-H]", a) and a not in kset):
                flag("答案键不在选项内", (qid, a, sorted(kset)[:8]))
        if typ == "single_choice" and len(ans) > 1:
            soft["单选题有多个答案"].append((qid, ans))
        if typ == "multiple_choice" and len(ans) < 2 and ans:
            soft["多选题答案不足2个"].append((qid, ans))
        if not ans:
            soft["无答案"].append(qid)
        if len(opts) < 2 and is_choice:
            soft["选择题选项不足2个"].append(qid)

    print(f"审计题目 {len(qs)} 题")
    print("\n【必须为 0】仍标“已核对”却结构不自洽（会污染正确率）")
    for k in ("题干为空", "选择题无选项", "选项键为空", "选项键重复", "答案键不在选项内"):
        v = hard.get(k) or []
        mark = "✅" if not v else "❌"
        print(f"  {mark} {k:20s} {len(v):6d}")
        for item in v[:3]:
            print(f"        {item}")
    print("\n【已隔离】结构缺陷但已降级为待核对（不进入正确率统计）")
    for k, v in quarantined.items():
        print(f"  {k:20s} {len(v):6d}")
    print("\n【软问题】原资料客观缺失，如实统计")
    for k, v in soft.items():
        print(f"  {k:20s} {len(v):6d}")

    out = {"total": len(qs),
           "hardVerified": {k: len(v) for k, v in hard.items()},
           "quarantined": {k: len(v) for k, v in quarantined.items()},
           "soft": {k: len(v) for k, v in soft.items()},
           "hardSamples": {k: v[:20] for k, v in hard.items()},
           "quarantinedSamples": {k: v[:20] for k, v in quarantined.items()}}
    json.dump(out, open(os.path.join(BANK, "integrity_audit.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("\n写出 work/bank/integrity_audit.json")
    hard_total = sum(len(v) for v in hard.values())
    quar_total = sum(len(v) for v in quarantined.values())
    print(f"污染正确率的硬错误合计 {hard_total}（必须为 0）；已隔离缺陷 {quar_total}")
    return 0 if hard_total == 0 else 2


if __name__ == "__main__":
    sys.exit(main())

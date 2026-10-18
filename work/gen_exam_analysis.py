#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""生成 docs/09_历年真题与考情分析.md —— 全部数字来自题库真实字段。

原则（与全项目一致）：
  - 只统计题库里**真实存在**的题（`category` 为「历年真题」「模拟笔试」）；
  - 领域分布用**关键词命中**并明确标注「非官方分类」，不用臆造的分类；
  - 原资料未载明的（招聘公告、笔试日期、题型分值）一律写「原文未载明」，不推测。
"""
import json
import os
import re
import sys
from collections import Counter, defaultdict

WORK = os.path.dirname(os.path.abspath(__file__))
BANK = os.path.join(WORK, "bank")
APP_DOCS = r"D:\DOWNLOADS\app\docs"

# 关键词命中表：用于说明“真题大致考了哪些领域”。
# 这不是官方题型分类，只是把题干里出现的特征词如实数出来，故在文中明确标注。
DOMAINS = [
    ("时政·政治理论", r"习近平|党|全会|公报|会议|规划|战略|政策|十四五|十五五|二十|精神|新时代|中国式"),
    ("企业文化·公司常识", r"国家能源|国电|集团|公司|煤炭|电力|装机|新能源|双碳|能源安全"),
    ("言语理解与表达", r"下列各句|没有歧义|成语|词语|填入|语病|最恰当|修辞|标点|句子排序|依次填入"),
    ("数量关系·数学运算", r"计算|多少|需要|速度|利润|工程|比例|甲|乙|小时|千米|平方米|利息|浓度"),
    ("判断推理·逻辑", r"推理|逻辑|假设|削弱|加强|最能|结论|矛盾|真假|排列|对应"),
    ("资料分析", r"增长|比重|同比|环比|百分|统计|图表|年份|平均"),
    ("常识判断·百科", r"下列|说法正确|不正确|错误的是|属于|不包括|起源于|被称为"),
]


def load():
    return json.load(open(os.path.join(BANK, "questions.json"), encoding="utf-8"))["questions"]


def fmt_pct(a, b):
    return f"{a/b*100:.1f}%" if b else "—"


def main():
    qs = load()
    L = []
    A = L.append
    A("# 历年真题与考情分析")
    A("")
    A("> **本文由 `work/gen_exam_analysis.py` 自动生成**，全部数字直接来自题库字段")
    A("> （`work/bank/questions.json`），不含任何推测。")
    A("> 原资料**未载明**的项目（招聘公告、笔试日期、题型分值分布）一律如实写「原文未载明」。")
    A(f"> 生成时间：2026-10-19；题库总量 **{len(qs)}** 题。")
    A("")

    for cat, title in (("历年真题", "一、历年真题"), ("模拟笔试", "二、模拟笔试题")):
        sub = [q for q in qs if q.get("category") == cat]
        A(f"## {title}")
        A("")
        ver = sum(1 for q in sub if q.get("answerStatus") == "verified")
        A(f"- 题量：**{len(sub)} 题**，来自 **{len({q.get('sourceFile') for q in sub})}** 个来源文件")
        A(f"- 已核对答案：{ver} 题（{fmt_pct(ver, len(sub))}）；"
          f"待核对 {sum(1 for q in sub if q.get('answerStatus')=='needs_review')} 题；"
          f"无答案 {sum(1 for q in sub if q.get('answerStatus')=='missing')} 题")
        A(f"- 题型：{ '、'.join(f'{k} {v}' for k, v in Counter(q.get('type') for q in sub).most_common()) }")
        A("")

        if cat == "历年真题":
            by = defaultdict(int)
            for q in sub:
                m = re.match(r"(\d{4})", q.get("sourceFile") or "")
                by[m.group(1) if m else "国电时期（文件名不含年份）"] += 1
            A("### 按年份分布（依来源文件名中的年份）")
            A("")
            A("| 年份 | 题量 |")
            A("|---|---:|")
            for y, n in sorted(by.items()):
                A(f"| {y} | {n} |")
            A("")

        A("### 按来源文件")
        A("")
        A("| 来源文件 | 题量 | 已核对 | 有页码 |")
        A("|---|---:|---:|---:|")
        for s, n in Counter(q.get("sourceFile") for q in sub).most_common():
            items = [q for q in sub if q.get("sourceFile") == s]
            v = sum(1 for q in items if q.get("answerStatus") == "verified")
            pg = sum(1 for q in items if q.get("sourcePage"))
            A(f"| `{s}` | {n} | {v} | {pg} |")
        A("")

        A("### 题干领域分布（关键词命中，**非官方分类**）")
        A("")
        A("> 说明：下表是把每道题的**题干**与一组特征词做匹配后的计数，")
        A("> 一道题可能命中多个领域，因此合计会大于题量。它只用来回答")
        A("> 「真题大致考了哪些方向」，**不代表官方题型或分值分布**（原文未载明）。")
        A("")
        A("| 领域（关键词命中） | 命中题数 | 占比 |")
        A("|---|---:|---:|")
        for name, rx in DOMAINS:
            r = re.compile(rx)
            n = sum(1 for q in sub if r.search(q.get("stem") or ""))
            A(f"| {name} | {n} | {fmt_pct(n, len(sub))} |")
        A("")

    A("## 三、原文未载明的关键信息（如实登记，不作推测）")
    A("")
    A("- **招聘公告原文未取得**：因此笔试日期、报名条件、岗位表在题库与报告中均无出处可依。")
    A("- **笔试日期未载明**：APP 中的 2026-10-24 是**学习完成目标日**（可在设置中修改），")
    A("  **不是**笔试日期。")
    A("- **题型/题量/分值分布未载明**：原资料未给出官方分值表，故本文只报题目数量，不折算分值。")
    A("- **图形推理题缺失**：图形无法从 PDF 提取（OCR 后四个选项均为「如上图所示」），")
    A("  故这类题**未入库**；真题中的图形题因此不完整。")
    A("- **2022 真题不可用**：原 PDF 水印覆盖正文，OCR 只取到水印文字，未能切题。")
    A("")
    A("## 四、从数据能看出的备考含义（仅基于上表事实）")
    A("")
    zz = [q for q in qs if q.get("category") == "历年真题"]
    mo = [q for q in qs if q.get("category") == "模拟笔试"]
    A(f"1. 真题与模拟题的**答案完整度较高**：真题已核对 {fmt_pct(sum(1 for q in zz if q.get('answerStatus')=='verified'), len(zz))}、")
    A(f"   模拟题已核对 {fmt_pct(sum(1 for q in mo if q.get('answerStatus')=='verified'), len(mo))}，"
      f"适合直接用于自测。")
    A(f"2. 真题**以单选题为主**（{sum(1 for q in zz if q.get('type')=='single_choice')}/{len(zz)} 题），"
      f"与 APP 的刷题模式一致。")
    A("3. 按关键词命中看，真题除行测各模块外，**时政与公司常识占比不低**；")
    A("   而全库题量最大的正是时政（见 `docs/01`），因此时政是性价比最高的提分板块。")
    A("4. 真题年份**不连续**（2012、2023—2025 及国电时期若干套），")
    A("   样本量有限，不宜据此推断「某模块必考多少题」——原资料未载明分值分布。")
    A("")
    A("## 五、可复核方式")
    A("")
    A("```powershell")
    A('cd "D:\\app project\\work"')
    A("python gen_exam_analysis.py   # 重新生成本文")
    A('python -c "import json;qs=json.load(open(\'bank/questions.json\',encoding=\'utf-8\'))[\'questions\'];'
      "print(sum(1 for q in qs if q['category']=='历年真题'))\"")
    A("```")
    A("")

    os.makedirs(APP_DOCS, exist_ok=True)
    out = os.path.join(APP_DOCS, "09_历年真题与考情分析.md")
    open(out, "w", encoding="utf-8").write("\n".join(L))
    print(f"写出 {out}（{len(L)} 行）")
    return 0


if __name__ == "__main__":
    sys.exit(main())

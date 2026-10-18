#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Quick probe: how much text do sample PDFs yield? Detects scanned/image-only files."""
import os
import sys

from pypdf import PdfReader

ROOT = r"D:\DOWNLOADS\26国家能源集团通关资料"
samples = [
    r"9、国家能源集团招聘EPI通用能力练习题库\EPI综合能力500题\EPI综合能力测试-判断推理-试题.pdf",
    r"9、国家能源集团招聘EPI通用能力练习题库\EPI综合能力500题\常识200道试题.pdf",
    r"9、国家能源集团招聘EPI通用能力练习题库\4-1-EPI综合能力题库----常识题精选600道_.pdf",
    r"1、2025国家能源集团招聘考试知识点讲义和企业文化\国家能源集团招聘笔试知识点讲义_.pdf",
    r"1、2025国家能源集团招聘考试知识点讲义和企业文化\国家能源集团企业文化试题.pdf",
    r"5、【模拟试题】国家能源招聘笔试模拟试题\2025国家能源集团模拟笔试试题和答案解析（一）.pdf",
    r"6、【国家能源集团招聘】12-25年笔试真题\2025国家能源校招笔试真题（不含英语）完整版答案及解释.pdf",
    r"3、【行测知识】国家能源行测部分分题型刷题提分题库\数字推理350题及答案详解.pdf",
    r"3、【行测知识】国家能源行测部分分题型刷题提分题库\言语理解400题及答案详解.pdf",
    r"8、时政【全年持续更新】\【全国时政】全国时政热点（已更4月）\24-26年时政\2026年时政+试题\2026年1月时政试题179道.pdf",
    r"8、时政【全年持续更新】\【全国时政】全国时政热点（已更4月）\【重要会议】2025重要时政+文章考点\2026年\考点速记  2026年国务院政府工作报告.pdf",
    r"8、时政【全年持续更新】\【全国时政】全国时政热点（已更4月）\【重要会议】2025重要时政+文章考点\十五五规划建议考点速记\（试题）关于《中共中央关于制定国民经济和社会发展第十五个五年规划的建议》的说明（70题）-.pdf",
    r"8、时政【全年持续更新】\【全国时政】全国时政热点（已更4月）\【重要会议】2025重要时政+文章考点\二十届4中考点速记\考点速记  中国共产党第二十届中央委员会第四次全体会议公报.pdf",
    r"11、面试学习资料包\现象认知题目加解析.docx",
    r"2、【行测知识】国家能源行测部分解题技巧方法汇总\数字推理类题型解题技巧讲义.pdf",
]

for rel in samples:
    p = os.path.join(ROOT, rel)
    name = os.path.basename(p)
    if not os.path.exists(p):
        print(f"MISSING {rel}")
        continue
    try:
        r = PdfReader(p)
        n = len(r.pages)
        total = 0
        empty = 0
        preview = ""
        for i, pg in enumerate(r.pages[:12]):
            t = (pg.extract_text() or "").strip()
            total += len(t)
            if not t:
                empty += 1
            if i < 2 and t and not preview:
                preview = t[:200].replace("\n", " / ")
        print(f"{name}\n   pages={n} chars(first12)={total} empty={empty}\n   {preview}\n")
    except Exception as e:
        print(f"{name}\n   ERROR {type(e).__name__}: {e}\n")

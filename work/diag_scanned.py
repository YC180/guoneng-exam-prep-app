#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""诊断：为什么这些文件没被 ocr.py 的 is_scanned() 选进 OCR 队列。"""
import os
import sys
import traceback

WORK = os.path.dirname(os.path.abspath(__file__))
ROOT = r"D:\DOWNLOADS\26国家能源集团通关资料"

FILES = [
    r"4、【专业知识】国家能源集团专业知识（近几年没考，可选看）\财会类\笔试知识点之--（财务类）会计学复习知识点讲义整理..pdf",
    r"4、【专业知识】国家能源集团专业知识（近几年没考，可选看）\财会类\笔试知识点之--（财务类）税法主要知识点总结..pdf",
    r"4、【专业知识】国家能源集团专业知识（近几年没考，可选看）\计算机类\1.计算机讲义\笔试知识点之--计算机类-操作系统复习资料.pdf",
    r"4、【专业知识】国家能源集团专业知识（近几年没考，可选看）\通信类\知识点之--（通信类）LTE基础知识.pdf",
    r"4、【专业知识】国家能源集团专业知识（近几年没考，可选看）\通信类\笔试知识点之--（通信类）通信网优试题题库.pdf",
    r"1、2025国家能源集团招聘考试知识点讲义和企业文化\【新版】新版国家能源企业文化核心理念\国家能源企业文化核心理念.pdf",
    r"11、面试学习资料包\8、面试题3000（赠送；时间多可参考看）\各省面试1000道.pdf",
    r"8、时政【全年持续更新】\【全国时政】全国时政热点（已更4月）\24-26年时政\2024年时政热点+试题\24年04月\2024年4时政热点试题及答案.pdf",
]

for rel in FILES:
    p = os.path.join(ROOT, rel)
    name = os.path.basename(rel)
    if not os.path.exists(p):
        print(f"{name[:52]:54s} 文件不存在")
        continue
    mb = os.path.getsize(p) / 1024 / 1024
    # pypdf（ocr.py 用的）
    try:
        from pypdf import PdfReader
        r = PdfReader(p)
        n = min(len(r.pages), 4)
        chars = 0
        for i in range(n):
            try:
                chars += len((r.pages[i].extract_text() or "").strip())
            except Exception:
                pass
        print(f"{name[:52]:54s} {mb:6.1f}MB pypdf总页={len(r.pages):3d} "
              f"前4页字符={chars:6d} is_scanned={chars < 60}")
    except Exception as exc:
        print(f"{name[:52]:54s} {mb:6.1f}MB pypdf 打开失败 → ocr.py 会静默判为"
              f"“非扫描件”而跳过 :: {type(exc).__name__}: {exc}")
    # PyMuPDF（提取用的）
    try:
        import pymupdf
        d = pymupdf.open(p)
        tot = 0
        for i in range(min(len(d), 4)):
            tot += len((d.load_page(i).get_text() or "").strip())
        print(f"{'':54s} PyMuPDF 总页={len(d):3d} 前4页字符={tot:6d}")
        d.close()
    except Exception as exc:
        print(f"{'':54s} PyMuPDF 失败 :: {type(exc).__name__}: {exc}")

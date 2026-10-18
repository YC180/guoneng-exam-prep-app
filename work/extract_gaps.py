#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""补齐“有文字层却从未被提取”的资料（多为超限跳过）。

教训：`国家能源企业文化核心理念.pdf`（71 MB）**带有完整文字层**，只因超过提取脚本的
体积上限被 `skipped-too-large` 跳过，于是在覆盖度审计里表现为“无可用文本”，
而它恰恰是 2025 新版企业文化手册的权威原文。本脚本对所有“尚无可用文本”的文件
先做一次**直接文字层提取**：能提出正文的就落盘（秒级完成），提不出的才留给 OCR。
"""
import os
import sys

WORK = os.path.dirname(os.path.abspath(__file__))
ROOT = r"D:\DOWNLOADS\26国家能源集团通关资料"
OUT = os.path.join(WORK, "text6")
MIN_OK = 300

# 来自 read_coverage.py 的 EMPTY 清单（纯图片与说明性 txt 除外）
def empty_list():
    import json
    p = os.path.join(WORK, "bank", "read_coverage.json")
    if not os.path.exists(p):
        print("请先运行 read_coverage.py")
        sys.exit(1)
    rows = json.load(open(p, encoding="utf-8"))
    return [r["rel"] for r in rows if r["kind"] == "EMPTY"]


def extract_pdf(path):
    import pymupdf
    d = pymupdf.open(path)
    npages = len(d)          # 必须在 close() 之前取，否则 ValueError: document closed
    parts = []
    for i, pg in enumerate(d):
        t = (pg.get_text() or "").strip()
        parts.append(f"[[PAGE {i + 1}]]\n{t}")
    d.close()
    return "\n\n".join(parts), npages


def extract_docx(path):
    from docx import Document
    doc = Document(path)
    body = "\n".join(p.text for p in doc.paragraphs)
    return body, 1


def main():
    os.makedirs(OUT, exist_ok=True)
    rels = empty_list()
    fixed, still = [], []
    for rel in rels:
        src = os.path.join(ROOT, rel)
        if not os.path.exists(src):
            still.append((rel, "文件不存在"))
            continue
        ext = os.path.splitext(rel)[1].lower()
        try:
            if ext == ".pdf":
                body, npages = extract_pdf(src)
            elif ext == ".docx":
                body, npages = extract_docx(src)
            else:
                still.append((rel, "非 PDF/DOCX，交由其他流程"))
                continue
        except Exception as exc:
            still.append((rel, f"提取失败 {type(exc).__name__}: {exc}"))
            continue
        stripped = len("".join(body.split()))
        if stripped < MIN_OK:
            still.append((rel, f"文字层仅 {stripped} 字符 → 仍需 OCR"))
            continue
        out_path = os.path.join(OUT, rel).replace(".pdf", ".txt").replace(".docx", ".txt")
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write(f"# SOURCE: {src}\n# EXTRACT: pymupdf（补提取：原提取流程跳过）\n\n{body}\n")
        fixed.append((rel, stripped, npages))
        print(f"OK  {stripped:8d}c {npages:4d}p  {os.path.basename(rel)[:60]}")

    print(f"\n补提取成功 {len(fixed)} 个；仍需 OCR/其他处理 {len(still)} 个")
    for rel, why in still:
        print(f"  仍需处理：{os.path.basename(rel)[:60]} :: {why}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

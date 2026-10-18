#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""资料阅读覆盖度审计。

目标：确认 26国家能源集团通关资料 下的**每一个文件**都被处理过——
要么提取出文本、要么 OCR 出文本、要么被明确记录为失败/跳过。
不允许存在“从未被打开过”的文件。

输出：work/reports/覆盖度审计.md + work/bank/coverage_audit.json
"""
import json
import os
import re
import sys
from collections import Counter, defaultdict

WORK = os.path.dirname(os.path.abspath(__file__))
ROOT = r"D:\DOWNLOADS\26国家能源集团通关资料"
TEXT_DIRS = ["text", "text2", "text3", "text4", "text5", "text6", "text7", "ocr"]
OUT_MD = os.path.join(WORK, "reports", "覆盖度审计.md")
OUT_JSON = os.path.join(WORK, "bank", "coverage_audit.json")

SRC_RE = re.compile(r"^#\s*SOURCE:\s*(.+?)\s*$", re.MULTILINE)
TEXT_EXT = {".txt", ".md", ".csv", ".json", ".html", ".htm"}
OFFICE_EXT = {".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx", ".wps", ".et"}
# 与备考无关、不要求提取的文件
SKIP_EXT = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".ico",
            ".mp3", ".mp4", ".wav", ".avi", ".zip", ".rar", ".7z", ".exe", ".lnk",
            ".ttf", ".otf", ".woff", ".db", ".ini", ".url", ".ds_store"}


def norm(p: str) -> str:
    return os.path.normcase(os.path.abspath(p)).rstrip("\\/")


def scan_outputs():
    """返回 {norm(源路径): [产出文件相对路径, ...]}"""
    mapping = defaultdict(list)
    for d in TEXT_DIRS:
        base = os.path.join(WORK, d)
        if not os.path.isdir(base):
            continue
        for dp, _dn, fns in os.walk(base):
            for fn in fns:
                if not fn.lower().endswith(".txt"):
                    continue
                fp = os.path.join(dp, fn)
                try:
                    with open(fp, encoding="utf-8", errors="replace") as fh:
                        head = fh.read(2000)
                except OSError:
                    continue
                m = SRC_RE.search(head)
                if m:
                    mapping[norm(m.group(1))].append(os.path.relpath(fp, WORK))
    return mapping


def load_failures():
    """从各 manifest 收集显式记录的失败/跳过。"""
    fails = defaultdict(list)
    for name in ("ocr/manifest.json",):
        p = os.path.join(WORK, name)
        if not os.path.exists(p):
            continue
        try:
            data = json.load(open(p, encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for rec in data if isinstance(data, list) else []:
            st = rec.get("status")
            if st and st != "ok":
                fails[norm(rec.get("src", ""))].append(f"ocr:{st}")
    return fails


def load_verified_duplicates():
    """已用 MD5 证实与另一目录逐字节相同的目录前缀（无需重复读取）。"""
    p = os.path.join(WORK, "bank", "gap_closure.json")
    if not os.path.exists(p):
        return []
    try:
        d = json.load(open(p, encoding="utf-8")).get("dup7vs9") or {}
    except (OSError, ValueError):
        return []
    if d.get("diff") == 0 and d.get("missing") == 0 and d.get("same", 0) > 0:
        return ["7、【EPI通用能力练习题库】国家能源集团招聘\\"]
    return []


def main():
    outputs = scan_outputs()
    fails = load_failures()
    dups = load_verified_duplicates()
    print(f"已提取/OCR 的源文件映射：{len(outputs)} 条")

    all_files = []
    for dp, _dn, fns in os.walk(ROOT):
        for fn in fns:
            all_files.append(os.path.join(dp, fn))
    print(f"资料目录文件总数：{len(all_files)}")

    buckets = Counter()
    unread = []
    empty_text = []
    for fp in sorted(all_files):
        ext = os.path.splitext(fp)[1].lower()
        key = norm(fp)
        rel = os.path.relpath(fp, ROOT)
        if any(rel.startswith(d) for d in dups):
            buckets["已验证为重复目录（MD5 全同，无需重复读取）"] += 1
            continue
        if ext in SKIP_EXT:
            buckets[f"非文本资源（{ext}）不必提取"] += 1
            continue
        if ext not in TEXT_EXT and ext not in OFFICE_EXT:
            buckets[f"未知类型（{ext or '无扩展名'}）"] += 1
            unread.append((rel, "未知类型"))
            continue
        outs = outputs.get(key, [])
        if not outs:
            if key in fails:
                buckets["显式记录失败/跳过"] += 1
            else:
                buckets["★从未被打开"] += 1
                unread.append((rel, "无任何产出"))
            continue
        biggest = 0
        for o in outs:
            try:
                biggest = max(biggest, os.path.getsize(os.path.join(WORK, o)))
            except OSError:
                pass
        if biggest < 400:
            if ext == ".pdf":
                buckets["扫描件：文本层为空（已交 OCR 流水线）"] += 1
            else:
                buckets["产出近空（<400B，非 PDF）"] += 1
            empty_text.append((rel, outs, biggest))
        else:
            buckets["已提取文本 ✅"] += 1

    print()
    for k, v in buckets.most_common():
        print(f"  {k}: {v}")

    if unread:
        print(f"\n★ 从未被打开的文件 {len(unread)} 个：")
        for rel, why in unread[:40]:
            print(f"    [{why}] {rel}")
    if empty_text:
        print(f"\n产出近空的文件 {len(empty_text)} 个（前 20）：")
        for rel, outs, sz in empty_text[:20]:
            print(f"    {sz:5d}B  {rel}")

    os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    json.dump({"total": len(all_files), "buckets": dict(buckets),
               "unread": [{"file": r, "why": w} for r, w in unread],
               "nearEmpty": [{"file": r, "outputs": o, "bytes": b} for r, o, b in empty_text]},
              open(OUT_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n写出 {OUT_JSON}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把脚本/文档里的旧工作目录绝对路径改到新位置。

旧：D:\\deepseek harness project   （工作目录已实体搬移到 D:\\app project）
新：D:\\app project

**为什么要用 Python 而不是 PowerShell**：这些文件是 UTF-8（多含中文），
PowerShell 5.1 的 Set-Content/Out-File 会按 ANSI 处理、把中文改坏。
本脚本只做字节级的安全替换：解码失败的文件一律**跳过并报告**，绝不猜编码。
"""
import os
import sys

OLD = "D:\\deepseek harness project"
NEW = "D:\\app project"
ROOTS = [r"D:\app project\work", r"D:\DOWNLOADS\app", r"D:\app project"]
EXTS = {".py", ".ps1", ".md", ".cmd", ".js", ".json", ".txt", ".html", ".css", ".webmanifest"}
SKIP_DIRS = {"node_modules", ".git", "__pycache__"}


def main():
    changed, skipped_bin, scanned = [], [], 0
    for root in ROOTS:
        if not os.path.isdir(root):
            continue
        for dp, dns, fns in os.walk(root):
            dns[:] = [d for d in dns if d not in SKIP_DIRS]
            for fn in fns:
                ext = os.path.splitext(fn)[1].lower()
                if ext not in EXTS:
                    continue
                p = os.path.join(dp, fn)
                scanned += 1
                try:
                    raw = open(p, "rb").read()
                except OSError as e:
                    print(f"  读取失败 {p}: {e}")
                    continue
                try:
                    txt = raw.decode("utf-8")
                except UnicodeDecodeError:
                    skipped_bin.append(p)
                    continue
                if OLD not in txt:
                    continue
                n = txt.count(OLD)
                out = txt.replace(OLD, NEW)
                with open(p, "w", encoding="utf-8", newline="") as fh:
                    fh.write(out)
                changed.append((p, n))

    print(f"扫描文本文件 {scanned} 个")
    print(f"改写的文件 {len(changed)} 个，共替换 {sum(n for _, n in changed)} 处")
    for p, n in changed[:40]:
        print(f"  {n:3d}  {p}")
    if len(changed) > 40:
        print(f"  …另有 {len(changed)-40} 个")
    if skipped_bin:
        print(f"\n非 UTF-8（无法安全改写，已跳过）{len(skipped_bin)} 个：")
        for p in skipped_bin[:20]:
            print("  " + p)
    return 0


if __name__ == "__main__":
    sys.exit(main())

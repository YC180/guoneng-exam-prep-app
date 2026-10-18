#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查交付目录里所有文本文件是否仍为正常 UTF-8（未被 GBK 误读二次编码）。

判定依据：GBK 误读 UTF-8 会产生大量「鍥/锛/鐨/鏂/涓/绗」这类汉字，正常中文技术文档
里几乎不会出现。任何文件命中即报错，绝不静默放过。
"""
import os
import sys

APP = r"D:\DOWNLOADS\app"
# GBK 误读 UTF-8 的典型“鬼字”。注意「涓」「绛」虽是候选，
# 但正常中文也会用（庞涓、绛云楼、杨绛、涓滴之力），故不计入。
MOJIBAKE = ["鍥", "锛", "鐨", "鏂", "绗", "鐢", "鏄", "鎴", "鏈", "鍜", "棰", "鍏"]
TEXT_EXT = {".md", ".js", ".json", ".html", ".css", ".webmanifest", ".cmd", ".ps1", ".svg", ".txt"}

bad, ok, skipped = [], 0, 0
for dp, dns, fs in os.walk(APP):
    dns[:] = [d for d in dns if d != "node_modules"]
    for fn in fs:
        ext = os.path.splitext(fn)[1].lower()
        if ext not in TEXT_EXT:
            skipped += 1
            continue
        p = os.path.join(dp, fn)
        raw = open(p, "rb").read()
        try:
            txt = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            bad.append((p, f"不是合法 UTF-8：{exc}"))
            continue
        if "\ufffd" in txt:
            bad.append((p, "含替换字符 U+FFFD"))
            continue
        # 单个「涓/绛」等字在正常中文里也会出现（庞涓、绛云楼、涓滴之力），
        # 因此用“数量 + 相邻组合”判定，避免误报。
        total = sum(txt.count(m) for m in MOJIBAKE)
        clusters = [txt[i:i + 2] for i in range(len(txt) - 1)
                    if txt[i] in MOJIBAKE and txt[i + 1] in MOJIBAKE]
        if total >= 6 or clusters:
            bad.append((p, f"疑似 GBK 误读二次编码：命中 {total} 次"
                           + (f"，相邻组合 {clusters[:4]}" if clusters else "")))
            continue
        ok += 1

print(f"检查完成：正常 {ok} 个，异常 {len(bad)} 个（跳过二进制 {skipped} 个）")
for p, why in bad:
    print(f"  ✗ {os.path.relpath(p, APP)} :: {why}")
if bad:
    print("\n存在异常文件，必须修复后才能交付。")
    sys.exit(1)
print("全部文本文件编码正常 ✅")

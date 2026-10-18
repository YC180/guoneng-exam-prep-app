#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Estimate the OCR workload: candidates, pages, and time."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ocr  # noqa: E402


def main():
    import pymupdf

    cands = ocr.collect(260.0)
    total_mb = sum(c["size_mb"] for c in cands)
    print(f"扫描件（无可提取文字）候选：{len(cands)} 个，共 {total_mb:.0f} MB\n")

    by_tier = {}
    grand_pages = 0
    for c in cands:
        try:
            d = pymupdf.open(c["src"])
            pages = len(d)
            d.close()
        except Exception as e:
            pages = -1
            print(f"  [读取失败] {c['rel'] if 'rel' in c else c['src']}: {e}")
        c["pages"] = pages
        if pages > 0:
            grand_pages += pages
        t = c["tier"]
        by_tier.setdefault(t, []).append(c)

    for t in sorted(by_tier):
        items = by_tier[t]
        pg = sum(x["pages"] for x in items if x["pages"] > 0)
        mb = sum(x["size_mb"] for x in items)
        print(f"【分级 {t}】{len(items)} 个文件，{pg} 页，{mb:.0f} MB，"
              f"预计 {pg * 4.0 / 3600:.1f} 小时")
        items.sort(key=lambda x: -x["pages"])
        for x in items[:8]:
            print(f"    {x['pages']:5d} 页  {x['size_mb']:7.1f} MB  {os.path.relpath(x['src'], ocr.ROOT)[:72]}")
        if len(items) > 8:
            print(f"    …… 其余 {len(items) - 8} 个文件")

    print(f"\n合计：{len(cands)} 个文件，{grand_pages} 页，"
          f"按 4 秒/页 约 {grand_pages * 4.0 / 3600:.1f} 小时（不含模型加载）")


if __name__ == "__main__":
    sys.exit(main())

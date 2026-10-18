#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Extract the official corporate-culture PDF (71 MB, text layer present).

It was previously skipped by the extractor's --max-mb cap, not because it was
a scan. Note: the 董事长寄语 in this booklet is signed 刘国跃, i.e. this is the
pre-2025 edition, superseded by the 2025 corporate-culture wording published on
ceic.com. Kept as the authoritative "old version" for comparison.
"""
import os
import sys

SRC = (r"D:\DOWNLOADS\26国家能源集团通关资料\1、2025国家能源集团招聘考试知识点讲义和企业文化"
       r"\【新版】新版国家能源企业文化核心理念\国家能源企业文化核心理念.pdf")
OUT = (r"D:\app project\work\text4"
       r"\新版企业文化核心理念（含刘国跃寄语，2025年前版本）.txt")


def main():
    from pypdf import PdfReader

    r = PdfReader(SRC)
    print(f"页数：{len(r.pages)}")
    parts = []
    empty = 0
    for i, pg in enumerate(r.pages):
        try:
            t = (pg.extract_text() or "").strip()
        except Exception as e:
            t = f"[提取失败: {e}]"
        if not t:
            empty += 1
        parts.append(f"[[PAGE {i + 1}]]\n{t}")
    body = "\n\n".join(parts)
    body = body.encode("utf-8", "replace").decode("utf-8")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(f"# SOURCE: {SRC}\n# 页数: {len(r.pages)}  空页: {empty}\n\n{body}\n")
    print(f"写出：{OUT}")
    print(f"字符数：{len(body)}，空页：{empty}")


if __name__ == "__main__":
    sys.exit(main())

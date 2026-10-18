#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""查询 text/text2 manifest 中特定文件的实际处理状态。"""
import json
import os
import sys

WORK = os.path.dirname(os.path.abspath(__file__))
KEYS = ["一号文件", "重要讲话考点预测", "政治局会议", "企业文化", "政治理论", "知识库"]


def main():
    for mf in ("text/manifest.json", "text2/manifest.json", "text4/面试/manifest.json",
               "text4/专业知识/manifest.json"):
        p = os.path.join(WORK, mf)
        if not os.path.exists(p):
            continue
        data = json.load(open(p, encoding="utf-8"))
        print(f"\n=== {mf}  共 {len(data)} 条")
        for rec in data:
            rel = rec.get("rel") or rec.get("src") or ""
            if any(k in rel for k in KEYS):
                print(f"  [{rec.get('status')}] chars={rec.get('chars')} "
                      f"err={rec.get('error','')} size={rec.get('size_mb')}  {rel[:88]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

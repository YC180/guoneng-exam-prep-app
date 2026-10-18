#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""One-page OCR sanity check before launching the full pipeline."""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

CANDIDATES = [
    r"D:\DOWNLOADS\26国家能源集团通关资料\1、2025国家能源集团招聘考试知识点讲义和企业文化",
    r"D:\DOWNLOADS\26国家能源集团通关资料\3、【行测知识】国家能源行测部分分题型刷题提分题库",
]


def find_pdf(root):
    for dp, _d, fs in os.walk(root):
        for n in sorted(fs):
            if n.lower().endswith(".pdf"):
                p = os.path.join(dp, n)
                if os.path.getsize(p) > 1024 * 200:
                    return p
    return None


def main():
    import fitz
    import numpy as np
    from rapidocr_onnxruntime import RapidOCR

    target = None
    for r in CANDIDATES:
        if os.path.isdir(r):
            target = find_pdf(r)
            if target:
                break
    if not target:
        print("找不到测试用 PDF")
        return 1

    print("测试文件：" + target)
    print("大小：%.1f MB" % (os.path.getsize(target) / 1024 / 1024))

    t0 = time.time()
    engine = RapidOCR()
    print("引擎加载：%.1f s" % (time.time() - t0))

    doc = fitz.open(target)
    print("页数：%d" % len(doc))

    for pno in (0, min(1, len(doc) - 1)):
        t1 = time.time()
        pix = doc.load_page(pno).get_pixmap(dpi=200)
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        if pix.n == 4:
            img = img[:, :, :3]
        res, _ = engine(img)
        dt = time.time() - t1
        texts = [r[1] for r in res] if res else []
        chars = sum(len(t) for t in texts)
        print("\n--- 第 %d 页：%d 个文本块，%d 字符，耗时 %.1f s ---" % (pno + 1, len(texts), chars, dt))
        print("\n".join(texts[:40]))
    doc.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

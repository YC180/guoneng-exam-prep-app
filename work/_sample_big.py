# -*- coding: utf-8 -*-
import os
import sys

sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]
from pypdf import PdfReader

base = r"D:\DOWNLOADS\26国家能源集团通关资料\11、面试学习资料包\8、面试题3000（赠送；时间多可参考看）"
for name in ["各省面试1000道.pdf", "面试大全1500题.pdf", "结构化面试经典100题.pdf"]:
    p = os.path.join(base, name)
    try:
        r = PdfReader(p)
        n = min(25, len(r.pages))
        tot = 0
        empty = 0
        for i in range(n):
            t = (r.pages[i].extract_text() or "").strip()
            tot += len(t)
            if not t:
                empty += 1
        print("%-32s pages=%-5d sampled=%-3d chars=%-7d empty=%d" % (name, len(r.pages), n, tot, empty))
    except Exception as e:
        print("%-32s ERR %s" % (name, e))

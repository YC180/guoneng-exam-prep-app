# -*- coding: utf-8 -*-
"""Final validation of the report."""
import os
import re
import sys

sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]
_LOG = open(r"D:\app project\work\_final_check.txt", "w", encoding="utf-8", newline="\n")
sys.stdout = _LOG

REPORT = r"D:\app project\work\reports\面试与专业知识归纳.md"
with open(REPORT, "r", encoding="utf-8") as fh:
    text = fh.read()

lines = text.split("\n")
print("总行数: %d" % len(lines))
print("总字符: %d" % len(text))
print("文件大小: %d 字节" % os.path.getsize(REPORT))
print("含 NUL 字节: %d" % text.count("\x00"))

heads = [(i + 1, l) for i, l in enumerate(lines) if re.match(r"^#{1,6} ", l)]
print("标题数: %d" % len(heads))
print("一级标题:")
for n, l in heads:
    if l.startswith("# "):
        print("   %5d %s" % (n, l))
print("二级标题:")
for n, l in heads:
    if l.startswith("## "):
        print("   %5d %s" % (n, l))

# duplicate heading text check
from collections import Counter
c = Counter(l.strip() for _n, l in heads)
dup = [(k, v) for k, v in c.items() if v > 1]
print("重复标题 (%d):" % len(dup))
for k, v in dup:
    print("   x%d %s" % (v, k))

# leftover assembly artifacts
print("残留分篇标题 (H1 from parts):")
for n, l in heads:
    if l.startswith("# ") and "归纳总结" not in l:
        print("   %5d %s" % (n, l))

# orphan headings right after a # or ## with no content
print("孤立/异常标题行:")
for i, l in enumerate(lines):
    if re.match(r"^#{1,6} ", l):
        nxt = lines[i + 1].strip() if i + 1 < len(lines) else ""
        if nxt.startswith("#"):
            print("   %5d %s  -> next is heading" % (i + 1, l))

print()
print("关键要求检查:")
checks = {
    "1 资料盘点": "## 1. 资料盘点" in text,
    "2 面试备考要点归纳": "## 2. 面试备考要点归纳" in text,
    "3 专业知识板块归纳": "## 3. 专业知识板块归纳" in text,
    "4 优先级建议": "## 4. 优先级建议" in text,
    "5 缺失／不可提取清单": "## 5. 缺失／不可提取清单" in text,
    "6 备考要点速查": "## 6. 备考要点速查" in text,
    "结构化面试": "结构化面试" in text,
    "半结构化面试": "半结构化面试" in text,
    "无领导小组": "无领导小组" in text,
    "测评要素": "测评要素" in text,
    "自我介绍": "自我介绍" in text,
    "着装": "着装" in text,
    "金句": "金句" in text,
    "电气": "电气" in text,
    "热能动力": "热能" in text,
    "计算机": "计算机" in text,
    "通信": "通信" in text,
    "财会": "财会" in text,
    "管理": "管理类" in text,
    "金融": "金融" in text,
    "中国电力与能源战略": "中国电力与能源战略" in text,
    "2026-10-24": "2026-10-24" in text,
    "近几年没考，可选看": "近几年没考，可选看" in text,
    "扫描件标注": "扫描件" in text,
    "不可提取": "不可提取" in text,
}
for k, v in checks.items():
    print("   [%s] %s" % ("OK " if v else "MISS", k))
_LOG.close()
print("done", file=sys.stderr)

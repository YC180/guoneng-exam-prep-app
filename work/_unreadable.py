# -*- coding: utf-8 -*-
"""Emit the definitive 'unreadable / not extracted' markdown table."""
import io
import json
import os
import sys

sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]
_OUT = open(r"D:\app project\work\_unreadable.txt", "w", encoding="utf-8", newline="\n")
sys.stdout = _OUT

MANIFESTS = [
    ("① 面试学习资料包", r"D:\app project\work\text4\面试\manifest.json"),
    ("② 专业知识", r"D:\app project\work\text4\专业知识\manifest.json"),
]

# A file counts as "not readable" when extraction yielded no usable Chinese body text.
MIN_CJK = 200


def body_cjk(path):
    """CJK chars in the body (after the SOURCE header block)."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError:
        return 0
    idx = text.find("[[PAGE 1]]")
    body = text[idx:] if idx >= 0 else text
    return sum(1 for ch in body if "\u4e00" <= ch <= "\u9fff")


stats = {}
for label, mpath in MANIFESTS:
    with open(mpath, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    rd = un = 0
    per = {}
    for r in data:
        st = r.get("status")
        out = r.get("out")
        cjk = body_cjk(out) if out and os.path.exists(out) else 0
        bad = st in ("skipped-too-large", "error") or cjk < MIN_CJK
        top = r["rel"].split("\\")[0] if "\\" in r["rel"] else "(根目录)"
        a, b = per.get(top, (0, 0))
        per[top] = (a + (0 if bad else 1), b + (1 if bad else 0))
        if bad:
            un += 1
        else:
            rd += 1
    stats[label] = (len(data), rd, un, per)
    print("### %s  条目=%d  可读=%d  不可读=%d" % (label, len(data), rd, un))
    for k in sorted(per):
        print("     %-24s 可读 %2d  不可读 %2d" % (k, per[k][0], per[k][1]))
print()

print("| # | 文件（相对子目录） | 体积 | 判定 |")
print("|---|---|---|---|")
n = 0
for label, mpath in MANIFESTS:
    with open(mpath, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    for r in sorted(data, key=lambda x: x["rel"]):
        st = r.get("status")
        out = r.get("out")
        cjk = body_cjk(out) if out and os.path.exists(out) else 0
        if st == "skipped-too-large":
            verdict = "超大文件，按体积上限跳过，**未提取**"
        elif st == "error":
            verdict = "提取报错，**未提取**"
        elif cjk < MIN_CJK:
            verdict = "图片型／扫描件，正文仅页码标记，**未提取文本**"
        else:
            continue
        n += 1
        print("| %d | `%s` | %.2f MB | %s |" % (n, r["rel"].replace("\\", "\\"), r.get("size_mb", 0), verdict))
print()
print("合计不可读：%d" % n)

# -*- coding: utf-8 -*-
"""Summarise extraction manifests for the report."""
import os
import sys

sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]
import json

MANIFESTS = {
    "面试": r"D:\app project\work\text4\面试\manifest.json",
    "专业知识": r"D:\app project\work\text4\专业知识\manifest.json",
}


def bucket(r):
    st = r.get("status")
    if st == "ok":
        return "ok"
    if st == "scanned-or-empty":
        return "scanned"
    if st == "skipped-too-large":
        return "too-large"
    if st == "error":
        return "error"
    return st or "?"


for label, path in MANIFESTS.items():
    if not os.path.exists(path):
        print("%s: NO MANIFEST" % label)
        continue
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    print("=" * 70)
    print("%s  entries=%d" % (label, len(data)))
    tot = sum(r.get("size_mb", 0) for r in data)
    print("  total size: %.1f MB" % tot)
    counts = {}
    for r in data:
        counts[bucket(r)] = counts.get(bucket(r), 0) + 1
    for k in sorted(counts):
        print("  %-12s %d" % (k, counts[k]))
    print("  -- NOT readable --")
    for r in data:
        b = bucket(r)
        if b in ("scanned", "too-large", "error"):
            print("   [%-11s] %6.1fMB %6dc  %s" % (b, r.get("size_mb", 0), r.get("chars", 0), r["rel"]))
    print("  -- readable (chars) --")
    for r in sorted([x for x in data if bucket(x) == "ok"], key=lambda x: -x.get("chars", 0)):
        print("   %7dc  %6.2fMB  %s" % (r.get("chars", 0), r.get("size_mb", 0), r["rel"]))

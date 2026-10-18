#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""打印题库与审计的关键数字（纯 ASCII 标签 + 计数，避免控制台编码干扰）。"""
import json
import os
from collections import Counter

WORK = os.path.dirname(os.path.abspath(__file__))
BANK = os.path.join(WORK, "bank")


def load(name):
    p = os.path.join(BANK, name)
    if not os.path.exists(p):
        return None
    return json.load(open(p, encoding="utf-8"))


def main():
    qs = load("questions.json")["questions"]
    print(f"TOTAL            {len(qs)}")
    st = Counter(q.get("answerStatus") for q in qs)
    for k, v in st.most_common():
        print(f"  status {k:16s} {v}")
    ty = Counter(q.get("type") for q in qs)
    for k, v in ty.most_common():
        print(f"  type   {k:16s} {v}")
    cat = Counter(q.get("category") for q in qs)
    for k, v in cat.most_common():
        print(f"  cat    {k:16s} {v}")
    print(f"has sourceFile   {sum(1 for q in qs if q.get('sourceFile'))}")
    print(f"has sourcePage   {sum(1 for q in qs if q.get('sourcePage'))}")
    print(f"OCR-tagged       {sum(1 for q in qs if 'OCR' in (q.get('tags') or []))}")
    print(f"no explanation   {sum(1 for q in qs if not q.get('explanation'))}")

    vr = load("validation_report.json")
    if vr:
        print("validation_report keys:", ", ".join(sorted(vr.keys())))
        for k in ("total", "final", "removed", "issues", "unanswerableDropped",
                  "crossChecked", "corroborated", "consistent", "conflicts"):
            if k in vr:
                v = vr[k]
                print(f"  {k:20s} {v if not isinstance(v, (list, dict)) else len(v)}")
        cc = vr.get("crossCheck")
        if isinstance(cc, dict):
            for k, v in cc.items():
                print(f"  crossCheck.{k:16s} {v if not isinstance(v, (list, dict)) else len(v)}")

    qa = load("quality_audit.json")
    if qa:
        print("quality_audit:", json.dumps({k: (len(v) if isinstance(v, list) else v)
                                           for k, v in qa.items()}, ensure_ascii=False)[:400])
    rc = load("read_coverage.json")
    if rc:
        print("read_coverage:", dict(Counter(r["kind"] for r in rc)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

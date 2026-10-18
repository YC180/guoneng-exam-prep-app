#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Inspect raw text head + first parsed questions for a source, to debug parsing."""
import sys

sys.path.insert(0, r"D:\app project\work")
import build_bank as bb  # noqa: E402


def show(fname, n_head=30, n_q=3, mode=None, ansfile=""):
    p = fname if fname.startswith("D:") else f"{bb.TEXT}\\{fname}"
    raw = open(p, encoding="utf-8", errors="replace").read()
    lines = bb.clean_lines(raw)
    print("=" * 100)
    print("SOURCE:", fname, " lines:", len(lines))
    print("-" * 40, "raw head")
    for l, pg in lines[:n_head]:
        print(f"  [{pg}] {l[:150]}")
    print("-" * 40, "option runs:", len(bb.option_runs(lines)))
    if mode == "unnumbered":
        qs = bb.parse_unnumbered(lines, {})
    elif mode == "numbered":
        qs = bb.parse_numbered(lines, {})
    elif mode == "pair":
        qs = bb.parse_pair(p, f"{bb.TEXT}\\{ansfile}", {})
    else:
        return
    print("-" * 40, "parsed:", len(qs))
    for q in qs[:n_q]:
        print(f"  type={q['type']} status={q['answerStatus']} ans={q['answer']}")
        print(f"  stem={q['stem'][:160]}")
        for o in q["options"][:6]:
            print(f"    {o['key']}. {o['text'][:80]}")
        print(f"  expl={q['explanation'][:160]}")


if __name__ == "__main__":
    show("2024国家能源校招笔试真题及参考答案1.txt", mode="numbered", n_head=40, n_q=2)
    show("2023国家能源集团夏招招聘在线笔试真题及答案解析.txt", mode="numbered", n_head=30, n_q=2)
    show("2025国家能源集团模拟笔试试题和答案解析（一）.txt", mode="numbered", n_head=30, n_q=2)
    show("EPI综合能力500题\\EPI综合能力测试-思维策略-试题.txt", mode="pair",
         ansfile="EPI综合能力500题\\EPI综合能力测试-思维策略-试题答案.txt", n_head=25, n_q=2)

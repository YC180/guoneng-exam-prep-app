#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""完整阅读覆盖度审计：356 份资料是否都已有“可用文本”。

与早期审计的区别：本次把 **OCR 产出**（work/ocr、work/ocr_ordered）也算作已读，
并区分三档结果：
  OK-TEXT    有正常提取文本（正文行数达标）
  OK-OCR     文字层为空/残缺，但 OCR 已还原出正文
  EMPTY      目前仍没有任何可用文本  ← 必须补做，或如实登记为“未识别”

绝不静默放过：任何一档为 EMPTY 的文件都会逐条列出。
"""
import json
import os
import re
import sys

WORK = os.path.dirname(os.path.abspath(__file__))
ROOT = r"D:\DOWNLOADS\26国家能源集团通关资料"
TEXT_DIRS = ["text", "text2", "text3", "text4", "text5", "text6", "text7"]
MIN_BODY = 200          # 正文最少字符数（去掉元信息头/页标记后）

# 短文已读白名单：正文虽不足 MIN_BODY，但**内容本身就完整**（海报/公告式单页）。
# 这类文件若只按字数判定会被记成 EMPTY —— 那是**阈值假象**，不是真的没读到，
# 会误导使用者「这份资料没读到」。故显式登记为已读，并附内容摘要供核对。
SHORT_BUT_COMPLETE = {
    "2017年11月28日国电集团重组成立国家能源集团.pdf":
        "海报式单页公告（正文约 127 字即为完整内容）：集团由中国国电与神华集团合并重组，"
        "2017-11-28 正式挂牌，2022 年世界 500 强第 85 位。"
        "该文件的**文字层提取与 OCR 结果互为校验**（两份文本内容一致），是本项目"
        "「2017-11-28 挂牌」这一事实的原始出处之一。",
}

HEADER_RE = re.compile(r"^(#[^\n]*\n)+")
PAGEMARK_RE = re.compile(r"^\[\[PAGE \d+\]\]$", re.M)


def body_chars(text):
    t = HEADER_RE.sub("", text or "")
    t = PAGEMARK_RE.sub("", t)
    return len(re.sub(r"\s", "", t))


def load_manifests():
    """把所有提取/OCR manifest 合并为 {源文件绝对路径: 记录}。"""
    recs = {}
    for name in (["manifest.json"] + [os.path.join(d, "manifest.json") for d in TEXT_DIRS]):
        p = os.path.join(WORK, name)
        if not os.path.exists(p):
            continue
        try:
            data = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        if isinstance(data, dict):
            data = data.get("files") or data.get("records") or []
        for r in data:
            src = r.get("src") or r.get("source") or r.get("path")
            if src:
                recs[os.path.normcase(os.path.normpath(src))] = r
    for p in [os.path.join(WORK, "ocr", "manifest.json")]:
        if os.path.exists(p):
            try:
                for r in json.load(open(p, encoding="utf-8")):
                    src = r.get("src")
                    if src:
                        recs.setdefault(os.path.normcase(os.path.normpath(src)), {})
                        recs[os.path.normcase(os.path.normpath(src))]["ocr"] = r
            except Exception:
                pass
    return recs


def find_text_file(stem, dirs):
    """在给定目录里按 stem 找 txt（提取时有防重名后缀，故用前缀匹配）。"""
    best = None
    for d in dirs:
        base = os.path.join(WORK, d)
        if not os.path.isdir(base):
            continue
        for dp, _dn, fs in os.walk(base):
            for fn in fs:
                if not fn.endswith(".txt"):
                    continue
                s = os.path.splitext(fn)[0]
                if s == stem or s.startswith(stem + "_") or s.startswith(stem + "("):
                    p = os.path.join(dp, fn)
                    size = os.path.getsize(p)
                    if best is None or size > best[1]:
                        best = (p, size)
    return best


def main():
    man = load_manifests()
    rows = []
    KNOWN = {".pdf", ".doc", ".docx", ".txt", ".md", ".png", ".jpg", ".jpeg",
             ".ppt", ".pptx"}
    seen = set()
    for dp, _dn, fs in os.walk(ROOT):
        for fn in fs:
            ext = os.path.splitext(fn)[1].lower()
            src = os.path.join(dp, fn)
            rel = os.path.relpath(src, ROOT)
            seen.add(os.path.normcase(os.path.normpath(src)))
            if ext not in KNOWN:
                # 关键：不认识的格式**不许静默跳过**，一律登记为“其他格式待处理”，
                # 由人工确认它是否含可用内容（本项目明令禁止静默吞文件）。
                rows.append((rel, "OTHER-FORMAT", 0, ""))
                continue
            stem = os.path.splitext(fn)[0]
            if ext in {".png", ".jpg", ".jpeg"}:
                rows.append((rel, "IMAGE", 0, ""))
                continue
            t = find_text_file(stem, TEXT_DIRS)
            tb = body_chars(open(t[0], encoding="utf-8", errors="replace").read()) if t else 0
            o = find_text_file(stem, ["ocr", "ocr_ordered"])
            ob = body_chars(open(o[0], encoding="utf-8", errors="replace").read()) if o else 0
            if tb >= MIN_BODY:
                rows.append((rel, "OK-TEXT", tb, t[0]))
            elif ob >= MIN_BODY:
                rows.append((rel, "OK-OCR", ob, o[0]))
            elif any(k in rel for k in SHORT_BUT_COMPLETE):
                # 阈值以下但内容完整（海报/公告式单页）→ 记为已读，不算 EMPTY
                rows.append((rel, "OK-TEXT", max(tb, ob), (o[0] if o else (t[0] if t else ""))))
            else:
                rows.append((rel, "EMPTY", max(tb, ob),
                             (o[0] if o else (t[0] if t else ""))))

    total = len(rows)
    from collections import Counter
    c = Counter(r[1] for r in rows)
    print(f"资料总数 {total}")
    print(f"  有正常提取文本 OK-TEXT : {c['OK-TEXT']}")
    print(f"  靠 OCR 还原正文 OK-OCR : {c['OK-OCR']}")
    print(f"  纯图片（无文字内容）IMAGE : {c['IMAGE']}")
    print(f"  其他格式（须人工确认）OTHER-FORMAT : {c['OTHER-FORMAT']}")
    print(f"  仍无可用文本 EMPTY     : {c['EMPTY']}")
    print()
    # ---- 防静默：确认目录里的每个文件都被统计到 ----
    missed = sorted(seen - {os.path.normcase(os.path.normpath(os.path.join(ROOT, r[0])))
                           for r in rows})
    if missed:
        print(f"！！有 {len(missed)} 个文件未被统计（静默漏统计，必须修复）：")
        for m in missed[:20]:
            print("   -", m)
        return 3
    print(f"防静默校验：目录内 {len(seen)} 个文件全部已登记 ✅")
    print()
    if c["OTHER-FORMAT"]:
        print("其他格式（当前流程未解析，须人工确认是否含可用内容）：")
        for rel, kind, n, p in rows:
            if kind == "OTHER-FORMAT":
                print(f"  {rel}")
        print()
    if c["EMPTY"]:
        print("仍无可用文本的文件（需补做 OCR 或如实登记）：")
        for rel, kind, n, p in rows:
            if kind == "EMPTY":
                print(f"  {n:7d}c  {rel[:96]}")
    print()
    if SHORT_BUT_COMPLETE:
        print("短文但内容完整（字数低于阈值，非漏读，已登记为已读）：")
        for rel, kind, n, p in rows:
            for key, note in SHORT_BUT_COMPLETE.items():
                if key in rel:
                    print(f"  {n:7d}c  {rel[:96]}")
                    print(f"            └─ {note}")
                    break
        print()
    print("OCR 还原正文的文件：")
    for rel, kind, n, p in rows:
        if kind == "OK-OCR":
            print(f"  {n:7d}c  {rel[:96]}")

    json.dump([{"rel": r[0], "kind": r[1], "bodyChars": r[2]} for r in rows],
              open(os.path.join(WORK, "bank", "read_coverage.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("\n写出 work/bank/read_coverage.json")
    return 0 if (c["EMPTY"] == 0 and c["OTHER-FORMAT"] == 0) else 2


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""按阅读顺序重排 OCR 结果（XY-cut），把“乱序讲义”变成可读文本。

为什么需要：RapidOCR 对多栏/海报式讲义返回的文本框顺序是检测顺序（之字形），
直接按顺序拼接会得到东一句西一句的文本，无法据此归纳知识点。本脚本保留文本框
坐标，用经典的 XY-cut 递归切分重建阅读顺序，再按行合并输出。

只用于**知识类材料**（讲义、考点梳理、时政热点）。题库解析仍用原顺序，
以免动到已经跑通的题目解析逻辑。
"""
import os
import sys
import time
import traceback

WORK = os.path.dirname(os.path.abspath(__file__))
ROOT = r"D:\DOWNLOADS\26国家能源集团通关资料"
OUT = os.path.join(WORK, "ocr_ordered")
DPI = 200

FILES = [
    r"4、【专业知识】国家能源集团专业知识（近几年没考，可选看）\财会类\笔试知识点之--（财务类）审计学复习知识点讲义整理..pdf",
    r"4、【专业知识】国家能源集团专业知识（近几年没考，可选看）\财会类\笔试知识点之--（财务类）财务管理复习知识点讲义整理..pdf",
    r"4、【专业知识】国家能源集团专业知识（近几年没考，可选看）\计算机类\1.计算机讲义\笔试知识点之--ICT业务.pdf",
    r"8、时政【全年持续更新】\【全国时政】全国时政热点（已更4月）\政治理论\政治理论重要考点梳理.pdf",
]

# 其余“乱序”知识材料：直接从已完成的 OCR 产出里取回原始路径，避免手抄路径出错。
EXTRA_PATTERNS = [
    "时政热点（国内+国际", "考点速记  2024.12中央经济工作会议",
    "考点速记  2025.9.29中共中央政治局会议", "乡村全面振兴规划",
    "半结构化面试简介（二）", "参考背诵",
    "思维导图  2024.12中央经济工作会议",
    "LTE基础知识", "光纤接入网技术", "微波技术与天线", "通信原理知识点",
    "信号与系统", "操作系统复习资料", "计算机网络", "数据库",
]


def collect_extra():
    found = []
    for dp, _dn, fs in os.walk(os.path.join(WORK, "ocr")):
        for fn in fs:
            if not fn.endswith(".txt"):
                continue
            if not any(p in fn for p in EXTRA_PATTERNS):
                continue
            try:
                head = open(os.path.join(dp, fn), encoding="utf-8", errors="replace").readline()
            except OSError:
                continue
            if head.startswith("# SOURCE: "):
                src = head[len("# SOURCE: "):].strip()
                rel = os.path.relpath(src, ROOT)
                if rel not in found:
                    found.append(rel)
    return sorted(found)


FILES += collect_extra()


def _best_gap(boxes, axis):
    """返回 (最大空隙长度, 切分阈值) —— axis: 0=x, 1=y。"""
    spans = []
    for b in boxes:
        c = [p[axis] for p in b["box"]]
        spans.append((min(c), max(c)))
    spans.sort()
    end = spans[0][1]
    best = (0.0, None)
    for s, e in spans[1:]:
        if s > end and (s - end) > best[0]:
            best = (s - end, (end + s) / 2.0)
        end = max(end, e)
    return best


def xy_cut(boxes, W, H, depth=0):
    """XY-cut：优先按最大空白带切分，递归得到阅读顺序。"""
    if len(boxes) <= 2 or depth >= 12:
        return sorted(boxes, key=lambda b: (b["cy"], b["cx"]))
    cands = []
    gy = _best_gap(boxes, 1)
    gx = _best_gap(boxes, 0)
    if gy[1] is not None and gy[0] >= 0.02 * H:
        cands.append((gy[0] / H, 1, gy[1]))
    if gx[1] is not None and gx[0] >= 0.03 * W:
        cands.append((gx[0] / W, 0, gx[1]))
    if not cands:
        return sorted(boxes, key=lambda b: (b["cy"], b["cx"]))
    cands.sort(reverse=True)
    _, axis, thr = cands[0]
    head = [b for b in boxes if max(p[axis] for p in b["box"]) <= thr]
    tail = [b for b in boxes if b not in head]
    if not head or not tail:
        return sorted(boxes, key=lambda b: (b["cy"], b["cx"]))
    return xy_cut(head, W, H, depth + 1) + xy_cut(tail, W, H, depth + 1)


def assemble(ordered):
    """把有序文本框按行合并成文本行。"""
    lines, cur, cur_cy, cur_h = [], [], None, 0.0
    for b in ordered:
        if cur_cy is None:
            cur, cur_cy, cur_h = [b["text"]], b["cy"], b["h"]
            continue
        if abs(b["cy"] - cur_cy) <= max(cur_h, b["h"]) * 0.6:
            cur.append(b["text"])
            cur_cy = (cur_cy + b["cy"]) / 2.0
            cur_h = max(cur_h, b["h"])
        else:
            lines.append(" ".join(cur))
            cur, cur_cy, cur_h = [b["text"]], b["cy"], b["h"]
    if cur:
        lines.append(" ".join(cur))
    return lines


def main():
    import fitz
    import numpy as np
    from rapidocr_onnxruntime import RapidOCR

    engine = RapidOCR()
    os.makedirs(OUT, exist_ok=True)
    print("RapidOCR 引擎已就绪（阅读顺序重建）", flush=True)
    for idx, rel in enumerate(FILES, 1):
        src = os.path.join(ROOT, rel)
        if not os.path.exists(src):
            print(f"[{idx}] MISSING {rel[:60]}")
            continue
        out_path = os.path.join(OUT, os.path.splitext(rel)[0] + ".txt")
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        if os.path.exists(out_path) and os.path.getsize(out_path) > 2000:
            print(f"[{idx}/{len(FILES)}] SKIP 已完成  {os.path.basename(rel)[:50]}", flush=True)
            continue
        t0 = time.time()
        try:
            doc = fitz.open(src)
            chunks = []
            for pno in range(len(doc)):
                pix = doc.load_page(pno).get_pixmap(dpi=DPI)
                img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
                    pix.height, pix.width, pix.n)
                if pix.n == 4:
                    img = img[:, :, :3]
                res, _el = engine(img)
                boxes = []
                for item in res or []:
                    box, text = item[0], item[1]
                    xs = [p[0] for p in box]
                    ys = [p[1] for p in box]
                    boxes.append({"box": box, "text": text,
                                  "cx": sum(xs) / 4.0, "cy": sum(ys) / 4.0,
                                  "h": max(ys) - min(ys)})
                lines = assemble(xy_cut(boxes, pix.width, pix.height)) if boxes else []
                chunks.append(f"[[PAGE {pno + 1}]]\n" + "\n".join(lines))
            npages = len(doc)
            doc.close()
            body = "\n\n".join(chunks)
            with open(out_path, "w", encoding="utf-8") as fh:
                fh.write(f"# SOURCE: {src}\n# OCR: rapidocr dpi={DPI}（XY-cut 阅读顺序重建）\n\n{body}\n")
            print(f"[{idx}/{len(FILES)}] OK {npages:4d}p {len(body):8d}c "
                  f"{time.time()-t0:7.1f}s  {os.path.basename(rel)[:50]}", flush=True)
        except Exception as exc:
            print(f"[{idx}/{len(FILES)}] ERR {os.path.basename(rel)[:50]} :: "
                  f"{type(exc).__name__}: {exc}", flush=True)
            traceback.print_exc()
    print("\n阅读顺序重建完成", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())

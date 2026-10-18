#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""OCR pipeline for scanned / image-only PDFs.

Renders pages with PyMuPDF and recognises Chinese text with RapidOCR
(PP-OCR models bundled in the wheel, no external tesseract binary needed).

Resumable: progress is recorded per source file in work/ocr/manifest.json, so
re-running skips finished files.

Usage:
  python ocr.py [--tier N] [--max-mb M] [--dpi 200] [--limit-files K]
"""
import argparse
import json
import os
import sys
import time
import traceback

ROOT = r"D:\DOWNLOADS\26国家能源集团通关资料"
WORK = r"D:\app project\work"
OUT = os.path.join(WORK, "ocr")

MAX_PIX = 24_000_000     # 单次送入模型的像素上限（超过则分块识别）
TILE = 2200              # 分块边长（像素）
OVERLAP = 200            # 相邻块重叠，避免切断文字行

# 价值分级：数字越小越优先
TIER_RULES = [
    (1, ["【新版】新版国家能源企业文化核心理念"]),
    (1, ["3、【行测知识】国家能源行测部分分题型刷题提分题库"]),
    (2, ["6、【国家能源集团招聘】12-25年笔试真题"]),
    (2, ["5、【模拟试题】"]),
    (3, ["8、时政【全年持续更新】"]),
    (4, ["1、2025国家能源集团招聘考试知识点讲义和企业文化"]),
    (5, ["10、国家能源集团概况"]),
    (6, ["11、面试学习资料包"]),
    (7, ["4、【专业知识】"]),
]


def tier_of(path: str) -> int:
    for t, keys in TIER_RULES:
        for k in keys:
            if k in path:
                return t
    return 9


def is_scanned(path: str, probe_pages: int = 4, threshold: int = 60) -> bool:
    """True when the PDF yields (almost) no extractable text.

    两条判定：
      1) 前若干页可提取字符数过少（阈值）；
      2) 文本层“极其稀疏” —— 例如 71 MB / 62 页却只有 1078 字符，实为图片型 PDF，
         但恰好带了几行页眉文字，只按阈值会被误判为“有文字”而**整个文件漏读**。
    读取失败时按“扫描件”处理（宁可多跑一次 OCR，也不静默漏读）。
    """
    try:
        from pypdf import PdfReader
        r = PdfReader(path)
        n = min(len(r.pages), probe_pages)
        if n == 0:
            return True
        total = 0
        for i in range(n):
            try:
                total += len((r.pages[i].extract_text() or "").strip())
            except Exception:
                pass
        if total < threshold:
            return True
        # 稀疏文本层：按全文件页数估算每页字符数
        try:
            npages = len(r.pages)
        except Exception:
            npages = n
        if npages > 20 and total / max(n, 1) < 120 and total / npages < 40:
            return True
        return False
    except Exception as exc:
        print(f"[warn] is_scanned 读取失败，按扫描件处理以免漏读：{path} :: "
              f"{type(exc).__name__}: {exc}", flush=True)
        return True


def collect(max_mb: float):
    cands = []
    for dirpath, _d, files in os.walk(ROOT):
        for n in sorted(files):
            if not n.lower().endswith(".pdf"):
                continue
            p = os.path.join(dirpath, n)
            mb = os.path.getsize(p) / 1024 / 1024
            if mb > max_mb:
                # huge files are almost always scans; keep them but flag
                pass
            if is_scanned(p):
                cands.append({"src": p, "size_mb": round(mb, 1), "tier": tier_of(p)})
    cands.sort(key=lambda c: (c["tier"], c["size_mb"]))
    return cands


def ocr_page(engine, img):
    """识别一页图像；超大页面（思维导图可达 2.7 亿像素）分块识别。

    RapidOCR 对超大输入会抛 ONNXRuntimeError，直接失败会白白丢掉整页内容。
    """
    h, w = img.shape[:2]
    if h * w <= MAX_PIX:
        try:
            res, _el = engine(img)
            return [r[1] for r in res] if res else []
        except Exception:
            pass
    texts = []
    for yi, y0 in enumerate(range(0, h, TILE - OVERLAP)):
        for xi, x0 in enumerate(range(0, w, TILE - OVERLAP)):
            tile = img[y0:min(h, y0 + TILE), x0:min(w, x0 + TILE)]
            if tile.shape[0] < 40 or tile.shape[1] < 40:
                continue
            try:
                res, _el = engine(tile)
            except Exception as exc:
                texts.append(f"[[分块 {yi},{xi} 识别失败：{type(exc).__name__}]]")
                continue
            if res:
                texts.extend(r[1] for r in res)
    return texts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tier", type=int, default=99, help="只处理 <= 该分级的文件")
    ap.add_argument("--max-mb", type=float, default=260.0)
    ap.add_argument("--dpi", type=int, default=200)
    ap.add_argument("--limit-files", type=int, default=0)
    ap.add_argument("--max-pages", type=int, default=0, help="0 = 全部")
    args = ap.parse_args()

    os.makedirs(OUT, exist_ok=True)
    man_path = os.path.join(OUT, "manifest.json")
    manifest = []
    if os.path.exists(man_path):
        try:
            manifest = json.load(open(man_path, encoding="utf-8"))
        except Exception:
            manifest = []
    done = {m["src"] for m in manifest if m.get("status") == "ok"}

    cands = [c for c in collect(args.max_mb) if c["tier"] <= args.tier]
    todo = [c for c in cands if c["src"] not in done]
    if args.limit_files:
        todo = todo[:args.limit_files]
    print(f"扫描件候选 {len(cands)} 个，待处理 {len(todo)} 个", flush=True)

    if not todo:
        print("没有待处理文件。")
        return

    import fitz  # PyMuPDF
    import numpy as np
    from rapidocr_onnxruntime import RapidOCR

    engine = RapidOCR()
    print("RapidOCR 引擎已就绪", flush=True)

    t_start = time.time()
    for idx, c in enumerate(todo, 1):
        src = c["src"]
        rel = os.path.relpath(src, ROOT)
        out_path = os.path.join(OUT, os.path.splitext(rel)[0] + ".txt")
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        rec = {"src": src, "rel": rel, "size_mb": c["size_mb"], "tier": c["tier"]}
        t0 = time.time()
        try:
            doc = fitz.open(src)
            npages = len(doc)
            if args.max_pages:
                npages = min(npages, args.max_pages)
            chunks = []
            empty = 0
            for pno in range(npages):
                page = doc.load_page(pno)
                pix = page.get_pixmap(dpi=args.dpi)
                img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
                    pix.height, pix.width, pix.n)
                if pix.n == 4:
                    img = img[:, :, :3]
                res_texts = ocr_page(engine, img)
                if not res_texts:
                    empty += 1
                chunks.append(f"[[PAGE {pno + 1}]]\n" + "\n".join(res_texts))
            doc.close()
            body = "\n\n".join(chunks)
            with open(out_path, "w", encoding="utf-8") as fh:
                fh.write(f"# SOURCE: {src}\n# OCR: rapidocr dpi={args.dpi}\n\n{body}\n")
            rec.update(status="ok", pages=npages, chars=len(body), empty_pages=empty,
                       out=out_path, seconds=round(time.time() - t0, 1))
            print(f"[{idx}/{len(todo)}] OK   {npages:4d}p {len(body):8d}c "
                  f"{rec['seconds']:7.1f}s  {rel[:70]}", flush=True)
        except Exception as exc:
            rec.update(status="error", error=f"{type(exc).__name__}: {exc}",
                       seconds=round(time.time() - t0, 1))
            print(f"[{idx}/{len(todo)}] ERR  {rel[:70]} :: {exc}", flush=True)
            traceback.print_exc()
        manifest.append(rec)
        with open(man_path, "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, ensure_ascii=False, indent=1)

    okc = sum(1 for m in manifest if m.get("status") == "ok")
    print(f"\n完成。累计成功 {okc} 个，用时 {(time.time() - t_start) / 60:.1f} 分钟")


if __name__ == "__main__":
    sys.exit(main())

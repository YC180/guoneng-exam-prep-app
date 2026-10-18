#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""补齐 OCR 队列之外的文件（含超大思维导图，走分块识别）。

为什么单独跑：主 OCR 队列（ocr.py）的 `is_scanned()` 以“前 4 页字符数”判定扫描件，
个别文件恰好带了几行页眉文字就被判为“有文字层”，于是既不进 OCR 队列、其文字层又
不足以归纳，成为覆盖盲区（例如 2017 重组公告、2024 年 4 月时政试题）。
思维导图类单页达 1 万 × 2.5 万像素，整页喂给 RapidOCR 会抛 ONNXRuntimeError，
本脚本用分块识别（ocr.ocr_page）处理。

输出与主 OCR 同目录、文件名不冲突，另记 gaps_manifest.json，不触碰主 manifest。
"""
import json
import os
import sys
import time
import traceback

WORK = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, WORK)
import ocr  # noqa: E402

DPI = 200

FILES = [
    r"8、时政【全年持续更新】\【全国时政】全国时政热点（已更4月）\24-26年时政\2024年时政热点+试题\24年04月\2024年4时政热点试题及答案.pdf",
    r"6、【国家能源集团招聘】12-25年笔试真题\2017年11月28日国电集团重组成立国家能源集团.pdf",
    r"8、时政【全年持续更新】\【全国时政】全国时政热点（已更4月）\【重要会议】2025重要时政+文章考点\2025年中央经济工作会议\思维导图  2025.12经济工作会议（合并）.pdf",
    r"8、时政【全年持续更新】\【全国时政】全国时政热点（已更4月）\【重要会议】2025重要时政+文章考点\二十届4中考点速记\思维导图  第二十届中央委员会第四次全体会议公报.pdf",
    r"8、时政【全年持续更新】\【全国时政】全国时政热点（已更4月）\【重要会议】2025重要时政+文章考点\2025年中央一号文件\思维导图  中共中央 国务院《关于进一步深化农村改革 扎实推进乡村全面振兴的意见》（合并）.pdf",
    r"8、时政【全年持续更新】\【全国时政】全国时政热点（已更4月）\【重要会议】2025重要时政+文章考点\2026年\思维导图  2026年国务院政府工作报告.pdf",
]


def main():
    import pymupdf
    import numpy as np
    from rapidocr_onnxruntime import RapidOCR

    engine = RapidOCR()
    man_path = os.path.join(ocr.OUT, "gaps_manifest.json")
    manifest = []
    if os.path.exists(man_path):
        try:
            manifest = json.load(open(man_path, encoding="utf-8"))
        except Exception:
            manifest = []
    done = {m["src"] for m in manifest if m.get("status") == "ok"}

    print("RapidOCR 引擎已就绪（补漏 + 分块）", flush=True)
    for idx, rel in enumerate(FILES, 1):
        src = os.path.join(ocr.ROOT, rel)
        if src in done:
            print(f"[{idx}/{len(FILES)}] SKIP 已完成  {os.path.basename(rel)[:50]}", flush=True)
            continue
        if not os.path.exists(src):
            print(f"[{idx}/{len(FILES)}] MISSING {os.path.basename(rel)[:60]}", flush=True)
            continue
        out_path = os.path.join(ocr.OUT, os.path.splitext(rel)[0] + ".txt")
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        t0 = time.time()
        rec = {"src": src, "rel": rel}
        try:
            doc = pymupdf.open(src)
            npages = len(doc)
            chunks, empty = [], 0
            for pno in range(npages):
                pix = doc.load_page(pno).get_pixmap(dpi=DPI)
                img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
                    pix.height, pix.width, pix.n)
                if pix.n == 4:
                    img = img[:, :, :3]
                texts = ocr.ocr_page(engine, img)
                if not texts:
                    empty += 1
                chunks.append(f"[[PAGE {pno + 1}]]\n" + "\n".join(texts))
            doc.close()
            body = "\n\n".join(chunks)
            with open(out_path, "w", encoding="utf-8") as fh:
                fh.write(f"# SOURCE: {src}\n# OCR: rapidocr dpi={DPI}（补漏；大页面分块）\n\n{body}\n")
            rec.update(status="ok", pages=npages, chars=len(body), empty_pages=empty,
                       seconds=round(time.time() - t0, 1))
            print(f"[{idx}/{len(FILES)}] OK {npages:4d}p {len(body):8d}c empty={empty} "
                  f"{rec['seconds']:7.1f}s  {os.path.basename(rel)[:48]}", flush=True)
        except Exception as exc:
            rec.update(status="error", error=f"{type(exc).__name__}: {exc}",
                       seconds=round(time.time() - t0, 1))
            print(f"[{idx}/{len(FILES)}] ERR {os.path.basename(rel)[:48]} :: "
                  f"{type(exc).__name__}: {exc}", flush=True)
            traceback.print_exc()
        manifest = [m for m in manifest if m.get("src") != src] + [rec]
        json.dump(manifest, open(man_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    ok = sum(1 for m in manifest if m.get("status") == "ok")
    err = [m for m in manifest if m.get("status") == "error"]
    print(f"\n补漏 OCR：成功 {ok}/{len(FILES)}，失败 {len(err)}", flush=True)
    for m in err:
        print(f"  失败：{os.path.basename(m['rel'])[:60]} :: {m.get('error')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

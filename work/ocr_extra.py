#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""补救 OCR：对文本层残缺（选项丢失 / 近乎空白）但仍未进入主 OCR 队列的文件做识别。

主 OCR 队列（ocr.py）判定“扫描件”的依据是文本层字符数，个别 PDF 文本层
“看似有文字、实则残缺”（如选项正文丢失），既不会被判为扫描件、也无法直接入题库。
本脚本对这些文件强制 OCR。
"""
import os
import sys
import time
import traceback

WORK = os.path.dirname(os.path.abspath(__file__))
ROOT = r"D:\DOWNLOADS\26国家能源集团通关资料"
OUT = os.path.join(WORK, "ocr")
DPI = 200
MAX_PIX = 24_000_000     # 单次送入模型的像素上限（超过则分块识别）
TILE = 2200              # 分块边长（像素）
OVERLAP = 200            # 相邻块重叠，避免切断文字行

FILES = [
    r"8、时政【全年持续更新】\【全国时政】全国时政热点（已更4月）\【重要会议】2025重要时政+文章考点\重要讲话包\❤【月更】24年-25年重要讲话考点预测400题（更新至25年7月底）.pdf",
    r"8、时政【全年持续更新】\【全国时政】全国时政热点（已更4月）\【重要会议】2025重要时政+文章考点\重要讲话包\❤【月更】24年-25年重要讲话考点预测400题（更新至25年7月底）-纯题本.pdf",
    r"8、时政【全年持续更新】\【全国时政】全国时政热点（已更4月）\【重要会议】2025重要时政+文章考点\重要讲话包\考点速记  2025.9.29中共中央政治局会议.pdf",
    # 双栏 PDF：文本层把两栏交错合并，选项正文错序（错序率 94%/97%），
    # 直接入库会产生“选项文字错乱”的题目，故改走 OCR。
    r"8、时政【全年持续更新】\【全国时政】全国时政热点（已更4月）\24-26年时政\2024年时政热点+试题\24年11月\2024年11月时事政治模拟题及答案（160题）.pdf",
    r"8、时政【全年持续更新】\【全国时政】全国时政热点（已更4月）\24-26年时政\2025年每月时政热点配套押题\6月押题\2025年6月时事政治模拟题及答案.pdf",
    # 文本层“近乎为空”（<400B）但确为图像内容的 PDF：普通提取只得到零星页眉，
    # 由覆盖度审计（bank/coverage_audit.json 的 nearEmpty）发现，补交 OCR。
    r"11、面试学习资料包\10、半结构化面试案例及解析（根据个人面试形式选择）\2.半结构化面试简介（二）.pdf",
    r"11、面试学习资料包\4、面试技巧+经验分享+总结+参考背诵\参考背诵1.pdf",
    r"11、面试学习资料包\4、面试技巧+经验分享+总结+参考背诵\参考背诵2.pdf",
    r"11、面试学习资料包\4、面试技巧+经验分享+总结+参考背诵\参考背诵3.pdf",
    r"8、时政【全年持续更新】\【全国时政】全国时政热点（已更4月）\【重要会议】2025重要时政+文章考点\2025年中央经济工作会议\思维导图  2025.12经济工作会议（合并）.pdf",
    r"8、时政【全年持续更新】\【全国时政】全国时政热点（已更4月）\【重要会议】2025重要时政+文章考点\中央经济工作会议时政\1思维导图  2024.12中央经济工作会议(1).pdf.pdf",
    r"8、时政【全年持续更新】\【全国时政】全国时政热点（已更4月）\【重要会议】2025重要时政+文章考点\二十届4中考点速记\思维导图  第二十届中央委员会第四次全体会议公报.pdf",
    r"8、时政【全年持续更新】\【全国时政】全国时政热点（已更4月）\政治理论\政治理论重要考点梳理.pdf",
    r"4、【专业知识】国家能源集团专业知识（近几年没考，可选看）\计算机类\1.计算机讲义\笔试知识点之--ICT业务.pdf",
    r"4、【专业知识】国家能源集团专业知识（近几年没考，可选看）\财会类\笔试知识点之--（财务类）审计学复习知识点讲义整理..pdf",
    r"4、【专业知识】国家能源集团专业知识（近几年没考，可选看）\财会类\笔试知识点之--（财务类）财务管理复习知识点讲义整理..pdf",
    r"4、【专业知识】国家能源集团专业知识（近几年没考，可选看）\通信类\知识点之--（通信类）LTE基础知识.pdf",
    r"4、【专业知识】国家能源集团专业知识（近几年没考，可选看）\通信类\笔试知识点之--ICT业务..pdf",
    r"4、【专业知识】国家能源集团专业知识（近几年没考，可选看）\通信类\笔试知识点之--（通信类）光纤接入网技术.pdf",
    r"4、【专业知识】国家能源集团专业知识（近几年没考，可选看）\通信类\笔试知识点之--（通信类）微波技术与天线_考试重点复习归纳.pdf",
    r"4、【专业知识】国家能源集团专业知识（近几年没考，可选看）\通信类\笔试知识点之--（通信类）通信原理知识点.pdf",
]


def _ocr_page(engine, img):
    """识别一页图像。

    超大页面（思维导图可达 1 万 × 2.5 万像素 ≈ 2.7 亿像素）直接喂给
    RapidOCR 会抛 ONNXRuntimeError，因此超过阈值时**分块识别**。
    """
    h, w = img.shape[:2]
    if h * w <= MAX_PIX:
        try:
            res, _el = engine(img)
            return [r[1] for r in res] if res else []
        except Exception:
            pass                      # 落到分块路径
    texts = []
    ys = list(range(0, h, TILE - OVERLAP))
    xs = list(range(0, w, TILE - OVERLAP))
    for yi, y0 in enumerate(ys):
        for xi, x0 in enumerate(xs):
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
    import fitz
    import numpy as np
    from rapidocr_onnxruntime import RapidOCR

    engine = RapidOCR()
    print("RapidOCR 引擎已就绪（补救任务）", flush=True)
    ok = 0
    for idx, rel in enumerate(FILES, 1):
        src = os.path.join(ROOT, rel)
        if not os.path.exists(src):
            print(f"[{idx}] MISSING {rel}")
            continue
        out_path = os.path.join(OUT, os.path.splitext(rel)[0] + ".txt")
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        if os.path.exists(out_path) and os.path.getsize(out_path) > 2000:
            print(f"[{idx}/{len(FILES)}] SKIP 已完成  {os.path.basename(rel)[:50]}", flush=True)
            ok += 1
            continue
        t0 = time.time()
        try:
            doc = fitz.open(src)
            chunks, empty = [], 0
            for pno in range(len(doc)):
                pix = doc.load_page(pno).get_pixmap(dpi=DPI)
                img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
                if pix.n == 4:
                    img = img[:, :, :3]
                res_texts = _ocr_page(engine, img)
                if not res_texts:
                    empty += 1
                chunks.append(f"[[PAGE {pno + 1}]]\n" + "\n".join(res_texts))
            npages = len(doc)
            doc.close()
            body = "\n\n".join(chunks)
            with open(out_path, "w", encoding="utf-8") as fh:
                fh.write(f"# SOURCE: {src}\n# OCR: rapidocr dpi={DPI} (rescue)\n\n{body}\n")
            ok += 1
            print(f"[{idx}/{len(FILES)}] OK {npages:4d}p {len(body):8d}c empty={empty} "
                  f"{time.time()-t0:7.1f}s  {os.path.basename(rel)[:50]}", flush=True)
        except Exception as exc:
            print(f"[{idx}/{len(FILES)}] ERR {os.path.basename(rel)[:50]} :: {type(exc).__name__}: {exc}")
            traceback.print_exc()
    print(f"\n补救 OCR 完成 {ok}/{len(FILES)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

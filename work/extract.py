#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Extract text from all PDF/DOCX/DOC/TXT under the reference material tree.

Usage:
  python extract.py --roots "<dir1>" "<dir2>" --out <outdir> [--max-mb N] [--include-filter substr]

Writes one .txt per source file (mirrored relative path) plus manifest.json.
Skips files larger than --max-mb (default 40MB) because those are usually
scanned image-only PDFs that pypdf cannot read anyway.
"""
import argparse
import json
import os
import re
import sys
import time
import traceback

SUPPORTED = {".pdf", ".docx", ".txt", ".md"}


def clean(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_pdf(path: str):
    from pypdf import PdfReader

    reader = PdfReader(path)
    pages = []
    empty = 0
    for i, page in enumerate(reader.pages):
        try:
            t = page.extract_text() or ""
        except Exception:
            t = ""
        t = clean(t)
        if not t:
            empty += 1
        pages.append(f"[[PAGE {i + 1}]]\n{t}")
    meta = {}
    try:
        if reader.metadata:
            for k in ("/Title", "/Author", "/CreationDate"):
                v = reader.metadata.get(k)
                if v:
                    meta[k] = str(v)
    except Exception:
        pass
    return "\n\n".join(pages), len(reader.pages), empty, meta


def extract_docx(path: str):
    import docx

    d = docx.Document(path)
    parts = [p.text for p in d.paragraphs]
    for tbl in d.tables:
        for row in tbl.rows:
            cells = [c.text.strip().replace("\n", " ") for c in row.cells]
            parts.append(" | ".join(cells))
    return clean("\n".join(parts)), None, 0, {}


def extract_txt(path: str):
    for enc in ("utf-8", "utf-8-sig", "gbk", "gb18030", "latin-1"):
        try:
            with open(path, "r", encoding=enc) as fh:
                return clean(fh.read()), None, 0, {"encoding": enc}
        except (UnicodeDecodeError, UnicodeError):
            continue
    return "", None, 0, {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--roots", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-mb", type=float, default=40.0)
    ap.add_argument("--include-filter", default=None)
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    manifest_path = os.path.join(args.out, "manifest.json")
    manifest = []
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, "r", encoding="utf-8") as fh:
                manifest = json.load(fh)
        except Exception:
            manifest = []
    done = {m["src"] for m in manifest}

    for root in args.roots:
        for dirpath, _dirnames, filenames in os.walk(root):
            for name in sorted(filenames):
                src = os.path.join(dirpath, name)
                ext = os.path.splitext(name)[1].lower()
                if ext not in SUPPORTED:
                    continue
                if src in done:
                    continue
                if args.include_filter and args.include_filter not in src:
                    continue
                size_mb = os.path.getsize(src) / (1024 * 1024)
                rel = os.path.relpath(src, root)
                rec = {
                    "src": src,
                    "rel": rel,
                    "ext": ext,
                    "size_mb": round(size_mb, 2),
                }
                if size_mb > args.max_mb:
                    rec.update(status="skipped-too-large", chars=0)
                    manifest.append(rec)
                    print(f"SKIP  ({size_mb:7.1f}MB) {rel}", flush=True)
                    continue
                t0 = time.time()
                try:
                    if ext == ".pdf":
                        text, npages, empty, meta = extract_pdf(src)
                        rec["pages"] = npages
                        rec["empty_pages"] = empty
                    elif ext == ".docx":
                        text, npages, empty, meta = extract_docx(src)
                    else:
                        text, npages, empty, meta = extract_txt(src)
                    rec["meta"] = meta
                except Exception as exc:
                    rec.update(
                        status="error",
                        error=f"{type(exc).__name__}: {exc}",
                        chars=0,
                    )
                    manifest.append(rec)
                    print(f"ERROR {rel}: {exc}", flush=True)
                    continue
                out_rel = os.path.splitext(rel)[0] + ".txt"
                out_path = os.path.join(args.out, out_rel)
                os.makedirs(os.path.dirname(out_path), exist_ok=True)
                body = f"# SOURCE: {src}\n# SIZE_MB: {size_mb:.2f}\n\n{text}\n"
                body = body.encode("utf-8", "replace").decode("utf-8")
                with open(out_path, "w", encoding="utf-8") as fh:
                    fh.write(body)
                rec.update(
                    status="ok",
                    chars=len(text),
                    out=out_path,
                    seconds=round(time.time() - t0, 2),
                )
                manifest.append(rec)
                with open(manifest_path, "w", encoding="utf-8") as fh:
                    json.dump(manifest, fh, ensure_ascii=False, indent=1)
                print(f"OK    {len(text):>8}c {rel}", flush=True)

    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=1)
    print("\nDONE manifest entries:", len(manifest))


if __name__ == "__main__":
    sys.exit(main())

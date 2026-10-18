#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Extract text for the 面试 + 专业知识 material sets.

Writes one .txt per source file (mirrored relative path) plus manifest.json.
- .pdf  -> pypdf (image-only PDFs yield ~0 chars and are recorded as scanned)
- .docx -> python-docx
- .doc  -> skipped here, converted separately via Word COM (see doc2txt.ps1)
- files > --max-mb are skipped as "too-large"
"""
import os
import sys

# The harness runs commands with cwd = the workspace root, which holds a shadowing
# inspect.py that breaks argparse. Remove that entry from sys.path *before* the
# stdlib is imported, while keeping entries that are legitimately stdlib dirs.
_script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [
    p
    for p in sys.path
    if os.path.abspath(p or ".") != _script_dir
    or os.path.exists(os.path.join(_script_dir, "argparse.py"))
]

import argparse
import json
import re
import time

SUPPORTED = {".pdf", ".docx", ".txt"}


def clean(text):
    if not text:
        return ""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_pdf(path):
    from pypdf import PdfReader
    reader = PdfReader(path)
    pages, empty = [], 0
    for i, page in enumerate(reader.pages):
        try:
            t = clean(page.extract_text() or "")
        except Exception:
            t = ""
        if not t:
            empty += 1
        pages.append("[[PAGE %d]]\n%s" % (i + 1, t))
    return "\n\n".join(pages), len(reader.pages), empty


def extract_docx(path):
    import docx
    d = docx.Document(path)
    parts = [p.text for p in d.paragraphs]
    for tbl in d.tables:
        for row in tbl.rows:
            parts.append(" | ".join(c.text.strip().replace("\n", " ") for c in row.cells))
    return clean("\n".join(parts)), None, 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-mb", type=float, default=25.0)
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    mpath = os.path.join(args.out, "manifest.json")
    manifest = []
    done = set()
    if os.path.exists(mpath):
        try:
            with open(mpath, "r", encoding="utf-8") as fh:
                manifest = json.load(fh)
            # retry previously failed entries; keep everything else as done
            manifest = [m for m in manifest if m.get("status") not in ("error",)]
            done = {m["src"] for m in manifest}
        except Exception:
            manifest = []

    for dirpath, _d, filenames in os.walk(args.root):
        for name in sorted(filenames):
            src = os.path.join(dirpath, name)
            ext = os.path.splitext(name)[1].lower()
            if ext not in SUPPORTED or src in done:
                continue
            size_mb = os.path.getsize(src) / (1024 * 1024)
            rel = os.path.relpath(src, args.root)
            rec = {"src": src, "rel": rel, "ext": ext, "size_mb": round(size_mb, 2)}
            if size_mb > args.max_mb:
                rec.update(status="skipped-too-large", chars=0)
                manifest.append(rec)
                print("SKIP  (%7.1fMB) %s" % (size_mb, rel), flush=True)
                continue
            t0 = time.time()
            try:
                if ext == ".pdf":
                    text, npages, empty = extract_pdf(src)
                    rec["pages"] = npages
                    rec["empty_pages"] = empty
                else:
                    text, npages, empty = extract_docx(src)
            except Exception as exc:
                rec.update(status="error", error="%s: %s" % (type(exc).__name__, exc), chars=0)
                manifest.append(rec)
                print("ERROR %s : %s" % (rel, exc), flush=True)
                continue
            out_path = os.path.join(args.out, os.path.splitext(rel)[0] + ".txt")
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            body = "# SOURCE: %s\n# SIZE_MB: %.2f\n\n%s\n" % (src, size_mb, text)
            with open(out_path, "w", encoding="utf-8") as fh:
                fh.write(body)
            chars = len(text)
            status = "ok" if chars > 200 else ("scanned-or-empty" if ext == ".pdf" else "near-empty")
            rec.update(status=status, chars=chars, out=out_path, seconds=round(time.time() - t0, 2))
            manifest.append(rec)
            with open(mpath, "w", encoding="utf-8") as fh:
                json.dump(manifest, fh, ensure_ascii=False, indent=1)
            print("%-17s %8dc %s" % (status, chars, rel), flush=True)

    with open(mpath, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=1)
    print("\nDONE entries:", len(manifest))


if __name__ == "__main__":
    main()

import re, io
edits = [
    ("read_coverage.py",
     'TEXT_DIRS = ["text", "text2", "text3", "text4", "text5", "text6"]',
     'TEXT_DIRS = ["text", "text2", "text3", "text4", "text5", "text6", "text7"]'),
    ("coverage_audit.py",
     'TEXT_DIRS = ["text", "text2", "text3", "text4", "text5", "ocr"]',
     'TEXT_DIRS = ["text", "text2", "text3", "text4", "text5", "text6", "text7", "ocr"]'),
    ("try_parse.py",
     'for d in ("text", "text2", "text3", "text4", "text5", "text6", "ocr", "ocr_ordered"):',
     'for d in ("text", "text2", "text3", "text4", "text5", "text6", "text7", "ocr", "ocr_ordered"):'),
    ("find_unused_sources.py",
     'for d in ("text", "text2", "text4", "text5", "ocr"):',
     'for d in ("text", "text2", "text4", "text5", "text6", "text7", "ocr"):'),
    ("missing_d_check.py",
     'for d in ("text", "text2", "text5", "ocr", "text4"):',
     'for d in ("text", "text2", "text5", "ocr", "text4", "text6", "text7"):'),
    ("show_2017.py",
     'for d in ("text", "text2", "text3", "text4", "text5", "text6", "ocr", "ocr_ordered"):',
     'for d in ("text", "text2", "text3", "text4", "text5", "text6", "text7", "ocr", "ocr_ordered"):'),
]
for fn, old, new in edits:
    t = open(fn, encoding="utf-8").read()
    if old not in t:
        print(f"  ⚠️ 未找到目标串，跳过 {fn}")
        continue
    open(fn, "w", encoding="utf-8", newline="").write(t.replace(old, new, 1))
    print(f"  ✅ {fn}: 已加入 text7")

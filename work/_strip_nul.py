# -*- coding: utf-8 -*-
"""Strip NUL bytes (and other stray C0 controls) from extracted .txt files.

pypdf emits U+0000 for some PDF text runs; those make the .txt files look like
binary to text tools. This rewrites affected files in place (UTF-8, LF) and
records a repair note in the header.
"""
import os
import re
import sys

sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]

roots = [
    r"D:\app project\work\text4\面试",
    r"D:\app project\work\text4\专业知识",
]
CTRL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")

fixed = []
for root in roots:
    for dp, _d, fns in os.walk(root):
        for n in sorted(fns):
            if not n.lower().endswith(".txt") or n == "manifest.json":
                continue
            p = os.path.join(dp, n)
            with open(p, "rb") as fh:
                raw = fh.read()
            if b"\x00" not in raw and not CTRL.search(raw.decode("utf-8", "replace")):
                continue
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                text = raw.decode("gb18030", "replace")
            before = text.count("\x00")
            text = CTRL.sub("", text)
            text = re.sub(r"\n{4,}", "\n\n\n", text)
            if "# REPAIRED:" not in text:
                text = text.replace(
                    "# SIZE_MB:",
                    "# REPAIRED: stripped %d NUL/control chars (pypdf artifact); UTF-8 LF\n# SIZE_MB:" % before,
                    1,
                )
            with open(p, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(text)
            fixed.append((os.path.relpath(p, root), before, len(text)))

print("repaired %d files" % len(fixed))
for rel, n, ln in fixed:
    print("   nul=%-6d chars=%-8d %s" % (n, ln, rel))

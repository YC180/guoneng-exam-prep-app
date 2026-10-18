# -*- coding: utf-8 -*-
"""Convert a cp936-encoded report file to UTF-8 in place."""
import sys

p = sys.argv[1]
with open(p, "rb") as fh:
    raw = fh.read()
try:
    text = raw.decode("utf-8")
    enc = "utf-8"
except UnicodeDecodeError:
    text = raw.decode("gb18030", "replace")
    enc = "gb18030"
with open(p, "w", encoding="utf-8", newline="\n") as fh:
    fh.write(text)
print("decoded as %s, %d chars" % (enc, len(text)))

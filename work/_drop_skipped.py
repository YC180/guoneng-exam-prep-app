# -*- coding: utf-8 -*-
"""Drop skipped-too-large / error entries from a manifest so they get re-attempted."""
import json
import os
import sys

sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]

path = sys.argv[1]
with open(path, "r", encoding="utf-8") as fh:
    data = json.load(fh)
keep = [r for r in data if r.get("status") not in ("skipped-too-large", "error")]
dropped = len(data) - len(keep)
with open(path, "w", encoding="utf-8") as fh:
    json.dump(keep, fh, ensure_ascii=False, indent=1)
print("dropped %d of %d entries" % (dropped, len(data)))

import os, sys
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]
from pypdf import PdfReader

root = r"D:\DOWNLOADS\26国家能源集团通关资料\4、【专业知识】国家能源集团专业知识（近几年没考，可选看）"
bad = []
for dp, _d, fns in os.walk(root):
    for n in fns:
        if not n.lower().endswith(".pdf"):
            continue
        p = os.path.join(dp, n)
        if os.path.getsize(p) > 25 * 1024 * 1024:
            continue
        try:
            r = PdfReader(p)
            enc = r.is_encrypted
            ok = None
            if enc:
                try:
                    ok = r.decrypt("")
                except Exception as e:
                    ok = "EXC:%s" % e
            if enc:
                bad.append((os.path.relpath(p, root), ok))
        except Exception as e:
            bad.append((os.path.relpath(p, root), "READER-ERR:%s" % e))

print("encrypted count:", len(bad))
for rel, ok in bad:
    print("  ", ok, rel)

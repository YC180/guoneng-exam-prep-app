import os
old = "D:\\deepseek harness project"
EXTS = {".py",".ps1",".md",".cmd",".js",".json",".txt",".html",".css",".webmanifest"}
hits = []
for root in (r"D:\app project", r"D:\DOWNLOADS\app"):
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in {"node_modules",".git","__pycache__"}]
        for fn in fns:
            if os.path.splitext(fn)[1].lower() not in EXTS: continue
            p = os.path.join(dp, fn)
            try:
                t = open(p, encoding="utf-8").read()
            except (UnicodeDecodeError, OSError):
                continue
            if old in t:
                hits.append((p, t.count(old)))
print(f"仍引用旧路径的文件：{len(hits)} 个")
for p, n in hits[:20]:
    print(f"  {n}  {p}")

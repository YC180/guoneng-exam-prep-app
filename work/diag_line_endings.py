import subprocess, os
files = subprocess.run(["git", "-C", r"D:\app project", "status", "--porcelain"],
                       capture_output=True, text=True, encoding="utf-8").stdout
targets = []
for line in files.splitlines():
    if line.startswith(" M") or line.startswith("M "):
        p = line[3:].strip().strip('"')
        targets.append(p)
def committed_bytes(path):
    r = subprocess.run(["git", "-C", r"D:\app project", "show", "HEAD:" + path],
                       capture_output=True)
    return r.stdout
for p in targets:
    full = os.path.join(r"D:\app project", p)
    if not os.path.isfile(full):
        print(f"  {p}: 工作区不存在")
        continue
    work = open(full, "rb").read()
    head = committed_bytes(p)
    same_if_crlf_normalized = work.replace(b"\r\n", b"\n") == head.replace(b"\r\n", b"\n")
    print(f"  {p}")
    print(f"     工作区 {len(work):,} B（CRLF {work.count(bytes([13,10])):,} 处）｜"
          f"HEAD {len(head):,} B（CRLF {head.count(bytes([13,10])):,} 处）"
          f"｜{'仅行尾差异 ✅' if same_if_crlf_normalized else '内容不同 ⚠️'}")

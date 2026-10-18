import os
files = [r"D:\app project\work\gap_out.txt",
         r"D:\app project\work\text3\01企业文化\国家能源集团企业文化.txt"]
old = "D:\\deepseek harness project"
for p in files:
    raw = open(p, "rb").read()
    print(f"=== {p}")
    print(f"    体积 {len(raw):,} B")
    enc_used = None
    for enc in ("utf-8", "gbk", "gb18030", "utf-16"):
        try:
            t = raw.decode(enc)
            enc_used = enc
            break
        except UnicodeDecodeError:
            continue
    print(f"    可解码编码: {enc_used}")
    if enc_used:
        t = raw.decode(enc_used)
        n = t.count(old)
        print(f"    含旧路径: {n} 处")
        if n:
            open(p, "w", encoding=enc_used, newline="").write(t.replace(old, "D:\\app project"))
            print(f"    已按 {enc_used} 改写")

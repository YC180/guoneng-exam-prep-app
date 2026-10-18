import os, zipfile, datetime
APP = r"D:\DOWNLOADS\app"
TOP = "国家能源集团备考学习APP"
out = r"D:\DOWNLOADS\国家能源集团备考学习APP_2026-10-19.zip"
n = 0
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for root, dirs, files in os.walk(APP):
        dirs.sort()
        for f in sorted(files):
            p = os.path.join(root, f)
            rel = os.path.relpath(p, APP).replace("\\", "/")
            z.write(p, f"{TOP}/{rel}")
            n += 1
    # 附一份校验清单，便于解压后核对
    listing = []
    for root, dirs, files in os.walk(APP):
        dirs.sort()
        for f in sorted(files):
            p = os.path.join(root, f)
            listing.append(f"{os.path.relpath(p, APP).replace(chr(92),'/')}\t{os.path.getsize(p)}")
    z.writestr(f"{TOP}/文件清单.txt",
               "国家能源集团备考学习APP —— 文件清单（相对路径\\t字节数）\n"
               f"生成时间：{datetime.datetime.now():%Y-%m-%d %H:%M}\n"
               f"文件数：{n}\n\n" + "\n".join(listing) + "\n")
print(f"✅ 已封包：{out}")
print(f"   内含 {n} 个文件 + 1 份清单；体积 {os.path.getsize(out)/1024/1024:.2f} MB")

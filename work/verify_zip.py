import zipfile, os
z = r"D:\DOWNLOADS\国家能源集团备考学习APP_2026-10-19.zip"
with zipfile.ZipFile(z) as f:
    names = f.namelist()
    bad = f.testzip()
print(f"封包: {z}")
print(f"  条目数 {len(names)}；完整性检查: {'通过 ✅' if bad is None else '损坏 '+bad}")
print(f"  顶层目录: {sorted({n.split('/')[0] for n in names})}")
print(f"  体积 {os.path.getsize(z)/1024/1024:.2f} MB")
print("  结构：")
for n in sorted(names):
    if n.count('/') <= 1 and not n.endswith('/'):
        print("   ", n)
    elif '/docs/' in n:
        pass
print("  docs/:", len([n for n in names if '/docs/' in n]), "份")
print("  可选导入/:", len([n for n in names if '可选导入/' in n]), "个文件")

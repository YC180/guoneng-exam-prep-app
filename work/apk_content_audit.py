import io, os, zipfile
APK = r"D:\DOWNLOADS\国家能源集团备考APP-v1.0.0.apk"
APP = r"D:\DOWNLOADS\app"

z = zipfile.ZipFile(APK)
print("== APK 条目 ==")
for i in z.infolist():
    kind = "压缩" if i.compress_type == 8 else "存储"
    print(f"  {i.filename:28s} 原始 {i.file_size:>10,} B  压缩后 {i.compress_size:>9,} B  {kind}")

raw = z.read("assets/www.zip")
inner = zipfile.ZipFile(io.BytesIO(raw))
print(f"\n== 归档内 {len(inner.namelist())} 个条目：UTF-8 标记(EFS)与非 ASCII 名 ==")
non_ascii = 0
missing_flag = []
for info in inner.infolist():
    try:
        info.filename.encode("ascii")
        is_ascii = True
    except UnicodeEncodeError:
        is_ascii = False
        non_ascii += 1
    if not is_ascii and not (info.flag_bits & 0x800):
        missing_flag.append(info.filename)
print(f"  非 ASCII 名条目：{non_ascii} 个")
print(f"  其中缺少 UTF-8 标记的：{len(missing_flag)} 个 {missing_flag[:3]}"
      f"  → {'✅ 名字编码安全' if not missing_flag else '⚠️ 需注意'}")

print("\n== 归档内容与交付目录逐字节比对 ==")
bad = []
for info in inner.infolist():
    if info.is_dir():
        continue
    a = inner.read(info.filename)
    p = os.path.join(APP, info.filename.replace("/", os.sep))
    if not os.path.isfile(p):
        bad.append((info.filename, "交付目录缺此文件"))
        continue
    b = open(p, "rb").read()
    if a != b:
        bad.append((info.filename, f"字节不同 {len(a)} vs {len(b)}"))
print(f"  比对 {len([i for i in inner.infolist() if not i.is_dir()])} 个文件｜不一致 {len(bad)}")
for name, why in bad[:6]:
    print("   ❌", name, why)
print("  " + ("✅ APK 内应用与已通过全部测试的交付目录逐字节一致" if not bad else "❌ 存在差异"))

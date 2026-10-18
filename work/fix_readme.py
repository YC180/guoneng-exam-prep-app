import sys
p = r"D:\DOWNLOADS\app\README.md"
raw = open(p, "rb").read()
bom = raw.startswith(b"\xef\xbb\xbf")
if bom:
    raw = raw[3:]
txt = raw.decode("utf-8", errors="replace")
try:
    fixed = txt.encode("gbk").decode("utf-8")
except Exception as exc:
    print("反解失败:", exc)
    sys.exit(1)
out = open(r"D:\app project\work\readme_fixed.md", "w", encoding="utf-8", newline="")
out.write(fixed)
out.close()
print("BOM:", bom)
print("当前行数:", txt.count("\n") + 1, " 修复后行数:", fixed.count("\n") + 1)
print("修复后前 3 行:")
for line in fixed.split("\n")[:3]:
    print("   ", line[:100])
print("修复后含关键数字:", "11294 题" in fixed, "| 343 题" in fixed, "| 结构完整" in fixed)

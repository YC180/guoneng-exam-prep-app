p = r"D:\DOWNLOADS\app\README.md"
t = open(p, encoding="utf-8").read()
before = t.count("11285 题")
t = t.replace("约 14 MB，11285 题", "约 14 MB，11521 题")
t = t.replace("**11285 题**", "**11521 题**")
open(p, "w", encoding="utf-8", newline="").write(t)
print("目录树题量更新:", before, "→ 残留检查:", t.count("11285"))

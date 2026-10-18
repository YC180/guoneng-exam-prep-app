p = r"D:\DOWNLOADS\app\README.md"
t = open(p, encoding="utf-8").read()
n1 = t.count("附带 8 份整理报告"); n2 = t.count("8 份整理报告（详见下节）")
t = t.replace("附带 8 份整理报告", "附带 9 份整理报告")
t = t.replace("├─ docs/                   8 份整理报告（详见下节）",
              "├─ docs/                   9 份整理报告（详见下节）")
open(p, "w", encoding="utf-8", newline="").write(t)
print("替换:", n1, n2, "→ 残留 '8 份':", t.count("8 份"))

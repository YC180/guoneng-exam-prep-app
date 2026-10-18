p = r"D:\DOWNLOADS\app\README.md"
txt = open(p, "rb").read().decode("utf-8", errors="replace")
if txt.startswith("\ufeff"):
    txt = txt[1:]
out = []
for c in txt:
    try:
        out.append(c.encode("gbk"))
    except Exception:
        out.append(b"\xef\xbf\xbd")      # PUA 位置用 U+FFFD 占位
rec = b"".join(out).decode("utf-8", errors="replace")
open(r"D:\app project\work\readme_recovered.txt", "w", encoding="utf-8").write(rec)
print("恢复文本行数:", rec.count("\n") + 1, " 字符数:", len(rec))

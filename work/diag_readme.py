p = r"D:\DOWNLOADS\app\README.md"
raw = open(p, "rb").read()
print("BOM:", raw[:3] == b"\xef\xbb\xbf", " 字节数:", len(raw))
txt = raw.decode("utf-8", errors="replace")
pua = [(i, c) for i, c in enumerate(txt) if 0xE000 <= ord(c) <= 0xF8FF]
print("PUA 字符数:", len(pua))
for i, c in pua[:12]:
    print(f"   idx={i} U+{ord(c):04X}  上文={txt[max(0,i-14):i]!r}  下文={txt[i+1:i+14]!r}")
# 用 GBK 反解，PUA 位置用 '?' 顶替，看能恢复多少
fixed = []
for c in txt:
    try:
        fixed.append(c.encode("gbk"))
    except Exception:
        fixed.append(b"?")
b = b"".join(fixed)
print()
print("反解后行数:", b.decode("utf-8", errors="replace").count("\n") + 1)
for line in b.decode("utf-8", errors="replace").split("\n")[:6]:
    print("   ", line[:110])

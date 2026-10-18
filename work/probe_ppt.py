import os, re, sys
p = r"D:\DOWNLOADS\26国家能源集团通关资料\11、面试学习资料包\2、高分面试穿搭\01面试装着讲义(1).ppt"
print("文件存在:", os.path.exists(p), "大小 %.2f MB" % (os.path.getsize(p)/1048576))
# 1) 先看能不能用 PowerPoint COM 打开
try:
    import win32com.client as wc
    has_com = True
except Exception as e:
    has_com = False
    print("win32com 不可用:", e)
if has_com:
    try:
        app = wc.Dispatch("PowerPoint.Application")
        pres = app.Presentations.Open(p, WithWindow=False)
        n = pres.Slides.Count
        buf = []
        for i in range(1, n + 1):
            for sh in pres.Slides(i).Shapes:
                if sh.HasTextFrame and sh.TextFrame.HasText:
                    buf.append(sh.TextFrame.TextRange.Text)
        pres.Close(); app.Quit()
        txt = "\n".join(buf)
        print(f"PowerPoint COM 成功：{n} 页，文本 {len(txt)} 字符")
        print(txt[:300])
    except Exception as e:
        print("PowerPoint COM 失败:", type(e).__name__, e)
# 2) 兜底：从二进制里抠 UTF-16LE 中文串
raw = open(p, "rb").read()
cands = re.findall(rb"(?:[\x00-\xff][\x4e-\x9f]){4,}", raw)
cands += re.findall(rb"(?:[\x4e-\x9f][\x00-\xff]){4,}", raw)
out = []
for c in cands:
    for enc in ("utf-16-le", "gbk"):
        try:
            s = c.decode(enc)
        except Exception:
            continue
        if len(s) >= 4:
            out.append(s)
            break
print(f"\n二进制抠出候选串 {len(out)} 条，示例：")
for s in out[:12]:
    print("   ", s[:80].replace("\n", " "))

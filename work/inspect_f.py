import pymupdf, os, re
F = r"D:\DOWNLOADS\F"
files = []
for d in sorted(os.listdir(F), key=lambda x: int(x) if x.isdigit() else 99):
    p = os.path.join(F, d)
    if os.path.isdir(p):
        for f in os.listdir(p):
            files.append(os.path.join(p, f))
print(f"{'页数':>5} {'字符':>8} {'水印?':>7}  文件")
for p in files:
    try:
        doc = pymupdf.open(p)
        txt = "".join(doc[i].get_text("text") for i in range(len(doc)))
        body = re.sub(r"\s", "", txt)
        # 水印特征（此前 2021/2022 真题曾因水印污染被排除）
        wm = bool(re.search(r"Eun\.com|各大.{0,6}讲义|103202|微信号|公众号|加群", txt))
        print(f"{len(doc):5d} {len(body):8d} {'⚠️有' if wm else '无':>7}  {os.path.basename(p)}")
        doc.close()
    except Exception as e:
        print(f"{'--':>5} {'--':>8} 打开失败 {type(e).__name__}: {str(e)[:60]}  {os.path.basename(p)}")

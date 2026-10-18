import os, pymupdf
ROOT = r"D:\DOWNLOADS\26国家能源集团通关资料"
rel = r"1、2025国家能源集团招聘考试知识点讲义和企业文化\【新版】新版国家能源企业文化核心理念\国家能源企业文化核心理念.pdf"
d = pymupdf.open(os.path.join(ROOT, rel))
print("页数", len(d))
tot = 0
for i, pg in enumerate(d):
    t = (pg.get_text() or "").strip()
    tot += len(t)
    if i < 6 or len(t) > 40:
        print(f"  页{i+1:3d} 字符{len(t):5d} 图像{len(pg.get_images()):2d}  {t[:70]!r}")
print("全文件可提取字符合计:", tot)

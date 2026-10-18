import importlib.util, json, os, sys
spec = importlib.util.spec_from_file_location("oc", "ocr.py")
oc = importlib.util.module_from_spec(spec); sys.modules["oc"] = oc
try:
    spec.loader.exec_module(oc)
except SystemExit:
    pass

ROOT = r"D:\DOWNLOADS\26国家能源集团通关资料"
targets = [
 r"4、【专业知识】国家能源集团专业知识（近几年没考，可选看）\计算机类\2.计算机题库\计算机类习题集.pdf",
 r"4、【专业知识】国家能源集团专业知识（近几年没考，可选看）\通信类\笔试知识点之--（通信类）通信网优试题题库.pdf",
 r"6、【国家能源集团招聘】12-25年笔试真题\2017年11月28日国电集团重组成立国家能源集团.pdf",
]
print("== manifest 记录 ==")
mf = r"D:\app project\work\ocr\manifest.json"
m = json.load(open(mf, encoding="utf-8")) if os.path.exists(mf) else {}
recs = m if isinstance(m, list) else (m.get("files") or [])
seen = 0
for r in recs:
    if not isinstance(r, dict): continue
    rel = str(r.get("rel") or r.get("path") or "")
    for t in targets:
        if os.path.basename(t) in rel:
            print("  {0}  pages={1}  {2}  err={3}".format(
                r.get("status"), r.get("pages"), os.path.basename(rel), str(r.get("error"))[:70]))
            seen += 1
if not seen:
    print("  （三份均无记录 → 说明被 is_scanned 判定为“有文字层”或未进入候选）")

print("\n== 逐份诊断 ==")
import pymupdf
for t in targets:
    p = os.path.join(ROOT, t)
    mb = os.path.getsize(p) / 1024.0 / 1024.0
    print("\n--- {0}  ({1:.1f} MB)".format(os.path.basename(t), mb))
    try:
        d = pymupdf.open(p)
        npages = len(d)
        txt = 0
        for i in range(min(4, npages)):
            txt += len(d[i].get_text("text").strip())
        print("    页数 {0}；前4页可提取字符 {1}".format(npages, txt))
        print("    is_scanned -> {0}".format(oc.is_scanned(p)))
        try:
            pix = d[0].get_pixmap(dpi=200)
            print("    首页渲染成功 {0}x{1}".format(pix.width, pix.height))
        except Exception as e:
            print("    首页渲染失败: {0}: {1}".format(type(e).__name__, str(e)[:90]))
        d.close()
    except Exception as e:
        print("    打开失败: {0}: {1}".format(type(e).__name__, str(e)[:90]))

import os, json
ROOT = r"D:\DOWNLOADS\26国家能源集团通关资料"
allf = []
for dp, dn, fs in os.walk(ROOT):
    for f in fs:
        allf.append(os.path.relpath(os.path.join(dp, f), ROOT))
print("目录下文件总数:", len(allf))
exts = {}
for f in allf:
    e = os.path.splitext(f)[1].lower()
    exts[e] = exts.get(e, 0) + 1
print("扩展名:", exts)
rc = json.load(open("bank/read_coverage.json", encoding="utf-8"))
print("read_coverage 记录:", len(rc))
rcset = {r["rel"] for r in rc}
missing = sorted(set(allf) - rcset)
print("未被 read_coverage 统计的文件:", len(missing))
for m in missing[:20]:
    print("   -", m)
extra = sorted(rcset - set(allf))
print("read_coverage 里有但目录里没有:", extra[:10])

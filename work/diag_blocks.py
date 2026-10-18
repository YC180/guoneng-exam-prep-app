import re
p = r"D:\app project\work\ocr\6、【国家能源集团招聘】12-25年笔试真题\2021国家能源集团--秋招笔试真题及答案.txt"
t = open(p, encoding="utf-8").read()
lines = [l.rstrip() for l in t.split("\n")]
ANS = re.compile(r"^答案为\s*([A-H])")
idx = [i for i, l in enumerate(lines) if ANS.match(l.strip())]
print("答案为行数:", len(idx))
for k in (0, 5, 20, 40):
    if k >= len(idx):
        continue
    i = idx[k]
    start = idx[k-1] + 1 if k > 0 else max(0, i - 14)
    print(f"===== 第 {k+1} 个答案块（行 {start}..{i}）=====")
    for j in range(start, i + 1):
        s = lines[j].strip()
        if s:
            print(f"  [{len(s):3d}] {s[:96]}")
    print()

import re
p = r"D:\app project\work\ocr\6、【国家能源集团招聘】12-25年笔试真题\2021国家能源集团--秋招笔试真题及答案.txt"
t = open(p, encoding="utf-8").read()
pages = re.split(r"\[\[PAGE (\d+)\]\]", t)
pairs = [(int(pages[i]), pages[i+1]) for i in range(1, len(pages)-1, 2)]
print("页数:", len(pairs))
for n, b in pairs[:3]:
    print(f"--- 第 {n} 页 ({len(b)} 字符) ---")
    print(b.strip()[:500])
    print()
# 统计：像题目/选项的行有多少
lines = [l.strip() for l in t.split("\n") if l.strip()]
qn = sum(1 for l in lines if re.match(r"^\d{1,3}[.、]", l))
opt = sum(1 for l in lines if re.match(r"^[A-D][.、]", l))
ans = sum(1 for l in lines if "答案" in l)
print(f"总行 {len(lines)}；编号行 {qn}；选项行 {opt}；含“答案”行 {ans}")

import re
p = r"D:\app project\work\text6\1、2025国家能源集团招聘考试知识点讲义和企业文化\【新版】新版国家能源企业文化核心理念\国家能源企业文化核心理念.txt"
t = open(p, encoding="utf-8").read()
# 按页拆分，定位关键词所在页
pages = re.split(r"\[\[PAGE (\d+)\]\]", t)
pairs = [(int(pages[i]), pages[i+1]) for i in range(1, len(pages)-1, 2)]
for kw in ["品牌口号", "同心而动", "聚力生辉", "共享美好", "五强五优", "核心价值观"]:
    hits = [n for n, body in pairs if kw in body]
    print(f"{kw:8s} 出现在页 {hits[:8]}")
print()
for n, body in pairs:
    if 14 <= n <= 17:
        print(f"===== 第 {n} 页 =====")
        print(body.strip()[:900])
        print()

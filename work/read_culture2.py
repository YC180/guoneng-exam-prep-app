import re
p = r"D:\app project\work\text6\1、2025国家能源集团招聘考试知识点讲义和企业文化\【新版】新版国家能源企业文化核心理念\国家能源企业文化核心理念.txt"
t = open(p, encoding="utf-8").read()
pages = re.split(r"\[\[PAGE (\d+)\]\]", t)
pairs = [(int(pages[i]), pages[i+1]) for i in range(1, len(pages)-1, 2)]
for n, body in pairs:
    if 57 <= n <= 62:
        print(f"===== 第 {n} 页 =====")
        print(re.sub(r"\n{2,}", "\n", body.strip())[:1100])
        print()

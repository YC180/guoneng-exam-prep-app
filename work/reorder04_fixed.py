p = r"D:\DOWNLOADS\app\docs\04_行测EPI考点归纳.md"
t = open(p, encoding="utf-8").read()

HS = "### 3.5 2026-10-19 新入库：秋招常考易错 1000 题（4 册，实测）"
BODY = "- **文本可读**：上述全部题库与真题文件均为"
assert HS in t and BODY in t, "锚点缺失"
i = t.index(HS)
j = t.index(BODY, i)
block35 = t[i:j].rstrip("\n")                 # §3.5 整块（含其后的空行）
# 1) 原位恢复 §3.4 标题，正文紧随其后
t2 = t[:i].rstrip("\n") + "\n\n### 3.4 可读性总结\n\n" + t[j:]
# 2) 把 §3.5 整块挪到 §3.4 正文（例外4）之后
k = t2.index("- **例外 4（空字节）**")
k = t2.index("\n", k) + 1
t3 = t2[:k] + "\n" + block35 + "\n" + t2[k:]

# 断言：章节顺序必须是 3.1 3.2 3.3 3.4 3.5，且 §3.4/§3.5 各出现一次
import re
order = re.findall(r"^### (3\.\d)", t3, re.M)
assert order[:6] == ["3.1", "3.2", "3.3", "3.4", "3.5"], f"章节顺序异常: {order[:6]}"
assert t3.count("### 3.4 可读性总结") == 1 and t3.count(HS) == 1, "标题重复"
open(p, "w", encoding="utf-8", newline="").write(t3)
print("✅ docs/04 已重排；章节顺序:", " ".join(order[:6]))

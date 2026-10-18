import re
p = r"D:\DOWNLOADS\app\docs\04_行测EPI考点归纳.md"
t = open(p, encoding="utf-8").read()
# 把误插到 §3.4 之前的 §3.5 整块挪到 §3.4 之后
i = t.index("### 3.5 2026-10-19 新入库")
j = t.index("---\n\n## 4. 高频考点与提分优先级", i)
block = t[i:j]                       # §3.5 整块（到 §4 之前）
rest = t[:i] + t[j:]                 # 去掉 §3.5 后的正文
# 在 §3.4 段落末尾（§4 之前）重新插入 §3.4 标题 + 原 §3.4 正文 + §3.5
assert "### 3.4 可读性总结" not in rest, "§3.4 标题仍在，逻辑不符"
anchor = "- **例外 4（空字节）**"
k = rest.index(anchor)
k = rest.index("\n", k) + 1
fixed = (rest[:k]
         + "\n### 3.4 可读性总结\n\n"
         + rest[k:].lstrip("\n")[:0]      # 占位（保持结构清晰）
         + "")
# 更简单可靠：直接用字符串拼接还原
fixed = rest[:k].rstrip("\n") + "\n\n" + block.rstrip("\n") + "\n\n" + rest[k:].lstrip("\n")
# 但这样 §3.4 标题仍缺 → 把 block 里 §3.5 之前补上 §3.4 标题与原文
open(p, "w", encoding="utf-8", newline="").write(fixed)
print("已重排（注意：§3.4 标题需补）")

p = "gen_coverage_doc.py"
t = open(p, encoding="utf-8").read()
old = 'A("已并入语料库 `F_2026年10月新增14份\\\\` 统一处理；对应关系见")'
new = 'A("已并入语料库的 `F_2026年10月新增14份` 目录统一处理；对应关系见")'
assert old in t, "未命中目录名行"
t = t.replace(old, new, 1)
open(p, "w", encoding="utf-8", newline="").write(t)
print("✅ 已修掉目录名末尾反斜杠（避免 Markdown 转义反引号）")

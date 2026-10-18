import re
p = "gen_coverage_doc.py"
t = open(p, encoding="utf-8").read()
print("SOURCES_ROOT 是否已定义:", bool(re.search(r"^SOURCES_ROOT\s*=", t, re.M)))
print("cov 变量是否存在:", "cov =" in t or "cov=" in t)
for m in re.finditer(r"^\s*(cov|qs|SOURCES_ROOT|APP_DOCS)\s*=.*$", t, re.M):
    print("  ", m.group(0).strip()[:100])

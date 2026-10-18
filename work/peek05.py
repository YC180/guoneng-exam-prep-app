import re
t = open("05_面试与专业知识归纳.md", encoding="utf-8").read()
print("docs/05 总字符:", len(t))
for k in ["审计学", "财务管理", "ICT", "政治理论"]:
    for m in list(re.finditer(k, t))[:2]:
        s = max(0, m.start() - 120)
        print(f"\n--- [{k}] …{t[s:m.start()+160]}…")

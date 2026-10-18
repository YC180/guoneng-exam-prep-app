import re
for p in [r"D:\DOWNLOADS\app\data\questions.js", r"D:\DOWNLOADS\app\docs\05_面试与专业知识归纳.md"]:
    t = open(p, encoding="utf-8").read()
    print("====", p.split("\\")[-1], len(t), "字符")
    for ch in "涓绛":
        for m in list(re.finditer(re.escape(ch), t))[:3]:
            print(f"  [{ch}] …{t[max(0,m.start()-32):m.start()+32]}…")

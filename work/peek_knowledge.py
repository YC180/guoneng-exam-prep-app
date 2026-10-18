import re
t = open(r"D:\DOWNLOADS\app\data\knowledge.js", encoding="utf-8").read()
print("长度", len(t))
for kw in ["同心而动", "聚力生辉", "共享美好", "五强五优", "绿色发展", "核心价值观", "品牌口号", "刘国跃", "邹磊", "企业精神"]:
    idxs = [m.start() for m in re.finditer(kw, t)]
    print(f"{kw:8s} 命中 {len(idxs)}")
    for i in idxs[:2]:
        print(f"    …{t[max(0,i-110):i+90]}…".replace("\n", " "))

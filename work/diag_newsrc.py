import json
from collections import Counter
qs = json.load(open("bank/questions.json", encoding="utf-8"))["questions"]
keys = ["审计学", "财务管理", "LTE", "ICT", "光纤接入", "微波技术", "通信原理", "参考背诵",
        "半结构化", "政治理论", "通信网优", "电信基础", "计算机类习题集", "各省面试1000",
        "2024年4时政", "2017年11月28日", "思维导图", "信号与系统", "宽带网", "接入网",
        "混合光纤", "现代交换", "计算机网络重要", "通信基础", "数据库系统", "操作系统",
        "数据结构", "计算机组成", "会计学复习", "成本管理会计", "税法主要"]
for k in keys:
    hits = [q for q in qs if k in (q.get("sourceFile") or "")]
    if hits:
        ver = sum(1 for q in hits if q.get("answerStatus") == "verified")
        print(f"{k:14s} {len(hits):5d} 题 (verified {ver:5d})  例: {(hits[0].get('stem') or '')[:60]}")
print()
print("来源文件总数:", len(Counter(q.get('sourceFile') for q in qs)))

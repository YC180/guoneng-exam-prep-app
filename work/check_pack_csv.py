import csv
p = r"D:\DOWNLOADS\app\可选导入\专业知识练习题_计算机类.csv"
rows = [r for r in csv.reader(open(p, encoding="utf-8")) if r and not r[0].startswith("#")]
head, data = rows[0], rows[1:]
print("列头:", ",".join(head))
print("题数:", len(data))
print("\n随机抽 8 题题干：")
import random
random.seed(7)
for r in random.sample(data, 8):
    print("  -", r[2][:78])
print("\n题干长度分布：min", min(len(r[2]) for r in data), "max", max(len(r[2]) for r in data))
print("选项数分布:", {})
from collections import Counter
print(Counter(sum(1 for x in r[3:7] if x.strip()) for r in data))
print("答案分布:", Counter(r[7] for r in data).most_common(6))

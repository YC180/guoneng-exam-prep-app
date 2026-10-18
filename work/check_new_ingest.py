import json
from collections import Counter
qs = json.load(open("bank/questions.json", encoding="utf-8"))["questions"]
print("总题数:", len(qs))
# 1) 新增配对来源的入库贡献
keys = ["F_2026年10月新增14份", "校园招聘笔试题", "常考易错1000题"]
src = Counter(q.get("sourceFile","") for q in qs)
print("\n新增来源入库量：")
tot = 0
for s, n in src.most_common():
    if any(k in s for k in keys):
        print(f"  {n:5d}  {s}")
        tot += n
print(f"  合计 {tot} 题来自本次新增的 F 目录 14 份")
# 2) 分类与章节
ch = Counter(q.get("chapter","") for q in qs if any(k in q.get("sourceFile","") for k in keys))
print("\n新增题目的章节分布：")
for c, n in ch.most_common(): print(f"  {n:5d}  {c}")
# 3) 那道冲突题是否已降级
hit = [q for q in qs if "绿色金融" in q.get("stem","")]
print(f"\n『绿色金融』相关题 {len(hit)} 道：")
for q in hit:
    print(f"  [{q['answerStatus']}] 答案={q.get('answer')} 题干={q['stem'][:56]}")
    print(f"      解析={(q.get('explanation') or '')[:90]}")
# 4) 资料分析样例的解析前导句读是否已清理
z = [q for q in qs if "资料分析（易错1000题）" == q.get("chapter")]
print(f"\n资料分析题 {len(z)} 道；解析前 60 字样例：")
for q in z[:2]:
    print(f"  {(q.get('explanation') or '')[:60]}")

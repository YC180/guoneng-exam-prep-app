import os, sys
sys.path.insert(0, os.path.abspath("."))
import build_bank as B
base = os.path.join(B.WORK, "text7")
qp = os.path.join(base, "国家能源秋招常考易错1000题-资料分析-学生版.txt")
ap = os.path.join(base, "国家能源秋招常考易错1000题-资料分析-答案版.txt")
qs = B.parse_pair_strict(qp, ap, {}, label="资料分析")
print("严格口径产出:", len(qs), "题")
# 统计题号交集
ql = B.expand_inline_options(B.clean_lines(open(qp, encoding="utf-8", errors="replace").read()))
al = B.clean_lines(open(ap, encoding="utf-8", errors="replace").read())
st = B.question_starts_strict(ql)
items = {no for _i, no, _h in st}
ans = set(B.parse_numbered_afile(al))
print(f"严格题号 {len(items)} 个｜答案题号 {len(ans)} 个｜交集 {len(items & ans)} 个")
print("\n抽样 4 题（看题干与解析是否讲同一件事）：")
for i in (0, 1, 60, 200):
    if i >= len(qs): continue
    q = qs[i]
    print(f"\n  [{i+1}] 题干：{q['stem'][:88]}")
    print(f"      选项：{'／'.join(str(o.get('key'))+'.'+str(o.get('text'))[:18] for o in (q.get('options') or [])[:4])}")
    print(f"      答案：{q['answer']}  状态：{q['answerStatus']}")
    print(f"      解析：{(q.get('explanation') or '')[:110]}")

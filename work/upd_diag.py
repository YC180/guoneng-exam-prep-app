import re, io, sys
p = "diag_pair_modes.py"
t = open(p, encoding="utf-8").read()
# 结论词补上「答案选/应选/故答案选」等，并加入 strict 口径对比
t = t.replace(
    'r"(?:故本题答案为|本题答案为|故答案为|答案为|正确答案为|正确答案是|故选|因此选|故选择)"',
    'r"(?:故本题答案为|本题答案为|故答案为|答案选|应选|正确答案为|正确答案是|故选|因此选|故选择)"')
t = t.replace('print(f"{\'章节\':<26}{\'普通\':>6}{\'分段\':>6}',
              'print(f"{\'章节\':<26}{\'普通\':>6}{\'严格\':>6}')
t = t.replace('        sect = B.parse_pair_sectioned(qp, ap, {}, label=ch)',
              '        sect = B.parse_pair_strict(qp, ap, {}, label=ch)')
t = t.replace("'分段/可比':>9}{'分段/矛盾'", "'严格/可比':>9}{'严格/矛盾'")
open(p, "w", encoding="utf-8", newline="").write(t)
print("诊断脚本已更新为 strict 口径 + 更全的结论词")

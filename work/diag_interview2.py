import re, json
p = r"D:\app project\work\ocr\11、面试学习资料包\8、面试题3000（赠送；时间多可参考看）\各省面试1000道.txt"
t = open(p, encoding="utf-8").read()
lines = [l.strip() for l in t.split("\n") if l.strip() and not l.startswith("#")]

PROV = re.compile(r"^([\u4e00-\u9fa5]{2,8}(?:省|市|自治区|兵团)?)(?:公务员|事业单位)?面试真题解析")
SET_RE = re.compile(r"^套题([一二三四五六七八九十]{1,3})$")
provinces, cur, sets = [], None, 0
prov_sets = {}
for l in lines:
    m = PROV.match(l)
    if m:
        cur = m.group(1); provinces.append(cur); prov_sets.setdefault(cur, 0); continue
    if SET_RE.match(l) and cur:
        prov_sets[cur] += 1
print(f"省份/地区数: {len(prov_sets)}")
for k, v in prov_sets.items():
    print(f"  {k}: {v} 套")
# 题目行：问句 + 结构化标签
qs = [l for l in lines if re.search(r"[？?]$", l) and len(l) > 8]
tags = re.findall(r"【(.{2,10}?)】", t)
from collections import Counter
print(f"\n问句行 {len(qs)}；【】标签 {len(tags)} 种 {len(set(tags))}")
print("高频标签:", Counter(tags).most_common(10))
# 广告/水印行
ads = [l for l in lines if re.search(r"淘宝|上岸|公众号|资料库|微信", l)]
print(f"\n广告/水印行 {len(ads)}，样例:", ads[:4])
json.dump({"provinces": prov_sets, "questionLines": len(qs),
           "tags": Counter(tags).most_common(30), "adLines": len(ads)},
          open("interview_outline.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("\n写出 interview_outline.json")

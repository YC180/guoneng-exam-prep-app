import re
p = r"D:\app project\work\ocr\11、面试学习资料包\8、面试题3000（赠送；时间多可参考看）\各省面试1000道.txt"
t = open(p, encoding="utf-8").read()
lines = [l.strip() for l in t.split("\n") if l.strip()]
print("总行数:", len(lines))
# 统计题号形态
pat = {
    "阿拉伯题号 1.": r"^\d{1,4}\s*[.、]",
    "中文题号 一、": r"^[一二三四五六七八九十]{1,3}\s*[、.]",
    "问句结尾 ?": r"[？?]$",
    "含【】标签": r"【.+?】",
}
for k, rx in pat.items():
    print(f"  {k}: {sum(1 for l in lines if re.search(rx, l))}")
print("\n--- 前 25 行 ---")
for l in lines[:25]:
    print("  " + l[:100])

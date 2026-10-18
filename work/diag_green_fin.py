import re, os
base = r"D:\app project\work\text7"
q = open(os.path.join(base,"2023年国家能源集团秋季校园招聘笔试题-学生.txt"), encoding="utf-8").read()
a = open(os.path.join(base,"2023年国家能源集团秋季校园招聘笔试题-答案.txt"), encoding="utf-8").read()
# 在学生版里找该题题号
mq = re.search(r"\n\s*(\d{1,3})\s*[.、]\s*发展绿色金融", q)
print("学生版中该题题号:", mq.group(1) if mq else "未找到")
if mq:
    no = mq.group(1)
    print("\n学生版原文片段:")
    i = mq.start()
    print(q[i:i+360].strip()[:360])
    # 答案版对应题号
    print(f"\n=== 答案版第 {no} 题 ===")
    ma = re.search(r"\n\s*" + no + r"\s*[.、]?\s*【答案】(.{0,320})", a, re.S)
    print(ma.group(0).strip()[:340] if ma else "未找到该题号")
    # 答案版里所有提到绿色金融的题号
    print("\n答案版中所有提到『绿色金融』的题号位置:")
    for m in re.finditer(r"(\d{1,3})\s*[.、]?\s*【答案】[^\n]{0,400}", a):
        seg = m.group(0)
        if "绿色金融" in seg:
            print("  题号", m.group(1), "→", re.sub(r"\s+"," ",seg)[:150])

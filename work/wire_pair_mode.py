import io
p = "build_bank.py"
t = open(p, encoding="utf-8").read()
reps = [
    # 1) SOURCES_PAIR 元组加 mode
    ('#       (base, 题目文件, 答案文件, 类别, 章节, 标签)',
     '#       (base, 题目文件, 答案文件, 类别, 章节, 标签, 解析口径)\n'
     '#   解析口径：pair=按题号配对（题号全局连续、无表格污染）；\n'
     '#             pair_strict=严格题号行判据再按题号配对（材料含表格时必需）。'),
    ('     "历年真题", "2021年春季校招笔试真题", ["真题", "校招"]),',
     '     "历年真题", "2021年春季校招笔试真题", ["真题", "校招"], "pair"),'),
    ('     "历年真题", "2022年秋季校招笔试真题", ["真题", "校招"]),',
     '     "历年真题", "2022年秋季校招笔试真题", ["真题", "校招"], "pair"),'),
    ('     "历年真题", "2023年秋季校招笔试真题", ["真题", "校招"]),',
     '     "历年真题", "2023年秋季校招笔试真题", ["真题", "校招"], "pair"),'),
    ('     "EPI通用能力", "判断推理（易错1000题）", ["行测", "易错题"]),',
     '     "EPI通用能力", "判断推理（易错1000题）", ["行测", "易错题"], "pair"),'),
    ('     "EPI通用能力", "数量关系（易错1000题）", ["行测", "易错题"]),',
     '     "EPI通用能力", "数量关系（易错1000题）", ["行测", "易错题"], "pair"),'),
    ('     "EPI通用能力", "言语理解（易错1000题）", ["行测", "易错题"]),',
     '     "EPI通用能力", "言语理解（易错1000题）", ["行测", "易错题"], "pair"),'),
    ('     "EPI通用能力", "资料分析（易错1000题）", ["行测", "易错题", "材料需回原文"]),',
     '     "EPI通用能力", "资料分析（易错1000题）", ["行测", "易错题", "材料需回原文"],\n     "pair_strict"),'),
    # 2) 循环解包加 mode
    ('    for base_name, qf, af, cat, ch, tags in SOURCES_PAIR:\n'
     '        # 配对来源自带基目录：2026-10-19 新增的 F 目录 14 份放在 work/text7\n'
     '        jobs.append((os.path.join(WORK, base_name), qf, "pair", cat, ch, tags, af))',
     '    for base_name, qf, af, cat, ch, tags, pmode in SOURCES_PAIR:\n'
     '        # 配对来源自带基目录与解析口径：2026-10-19 新增的 F 目录 14 份放在 work/text7\n'
     '        jobs.append((os.path.join(WORK, base_name), qf, pmode, cat, ch, tags, af))'),
]
for old, new in reps:
    if old not in t:
        print("⚠️ 未找到:", old[:64].replace("\n", "\\n"))
        continue
    t = t.replace(old, new, 1)
open(p, "w", encoding="utf-8", newline="").write(t)
print("build_bank.py 已接入 pair_strict 口径")

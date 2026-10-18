import importlib.util, os, sys
spec = importlib.util.spec_from_file_location("bb", "build_bank.py")
bb = importlib.util.module_from_spec(spec)
sys.modules["bb"] = bb
spec.loader.exec_module(bb)

base = r"D:\app project\work\ocr\6、【国家能源集团招聘】12-25年笔试真题"
for fn in ("2021国家能源集团--秋招笔试真题及答案.txt",
           "2020国家能源集团--春招笔试真题及答案.txt"):
    p = os.path.join(base, fn)
    if not os.path.exists(p):
        print("缺失", fn); continue
    raw = open(p, encoding="utf-8").read()
    lines = bb.ocr_lines(raw)
    meta = {"sourceFile": fn}
    qs = bb.parse_answerline_blocks(lines, meta)
    print(f"=== {fn[:34]} ===")
    print(f"  采纳 {len(qs)} 题 | 水印丢弃 {bb.ANSBLOCK_STATS['skippedJunk']} | 形态不合 {bb.ANSBLOCK_STATS['skippedShape']}")
    bb.ANSBLOCK_STATS.update(kept=0, skippedJunk=0, skippedShape=0)
    for q in qs[:4]:
        print(f"   [{q['answerStatus']}] {q['answer']} 选项{len(q['options'])}  {q['stem'][:52]}")
        for o in q['options']:
            print(f"        {o['key']}. {o['text'][:40]}")
    print()

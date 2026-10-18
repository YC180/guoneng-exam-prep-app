import importlib.util, sys, os
spec = importlib.util.spec_from_file_location("bb", "build_bank.py")
bb = importlib.util.module_from_spec(spec); sys.modules["bb"] = bb; spec.loader.exec_module(bb)
p = r"D:\app project\work\ocr\3、【行测知识】国家能源行测部分分题型刷题提分题库\图形推理350题及答案详解.txt"
raw = open(p, encoding="utf-8", errors="replace").read()
lines = bb.ocr_lines(raw)
exp = bb.expand_inline_options([(bb.normalize_bare_option_letters(t), pg) for t, pg in lines])
qs = bb.parse_unnumbered(exp, {})
print("unnumbered 解析题数:", len(qs))
# 选项里“图”相关占多少
tot = sum(len(q["options"]) for q in qs)
fig = sum(1 for q in qs for o in q["options"] if "图" in o["text"] or "所示" in o["text"])
print(f"选项总数 {tot}，其中含“图/所示”的 {fig}（{fig/max(tot,1)*100:.1f}%）")
for q in qs[:6]:
    print(f"\n  [{q['answerStatus']}] {q['answer']}  {q['stem'][:70]}")
    for o in q["options"]:
        print(f"      {o['key']}. {o['text'][:46]}")

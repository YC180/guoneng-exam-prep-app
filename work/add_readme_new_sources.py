p = r"D:\DOWNLOADS\app\README.md"
t = open(p, encoding="utf-8").read()
anchor = "- 来源：`26国家能源集团通关资料` 全部 **370 份**文件均已登记处理，每题标注来源文件与页码，可回溯核对"
add = anchor + "\n" + (
    "- 本轮新增（2026-10-19）：14 份「学生版＋答案版」成对资料已入库 —— 3 套校招真题"
    "（2021 春 / 2022 秋 / 2023 秋）与 4 册「秋招常考易错 1000 题」"
    "（判断推理 / 数量关系 / 言语理解 / 资料分析）；解析 1197 题、与既有题库去重后**入库 803 题**。"
    "明细与可复核口径见 `docs/07` 第九节。")
assert anchor in t, "未找到来源行"
t = t.replace(anchor, add, 1)
open(p, "w", encoding="utf-8", newline="").write(t)
print("✅ README 已补本轮新增说明")

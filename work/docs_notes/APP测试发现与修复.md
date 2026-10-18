# APP 测试发现与修复记录

本文件记录**由测试脚本实测发现**的 APP 缺陷、根因、修法与复验证据。
与题库侧的口径一致：**发现的问题一律留痕，不悄悄改掉就完事**。

---

## 一、模拟考试「交卷成绩」分项重复计数（2026-10-19 发现并修复）

### 症状（用户可见）

成绩页会同时显示互相矛盾的数字，例如 100 题的考试出现：

```
未作答 94
答错   94
```

—— 94 题不可能既「未作答」又「答错」，且 94 + 94 + 正确数 > 总题数。

### 怎么发现的

在 `work/domtest/test.js` 里给交卷结果加了一条**自洽断言**：

```js
assert(r.correct + r.wrong + r.unanswered + r.unverified === r.total,
  '成绩分项之和应等于总题数');
```

它不是「看页面能不能渲染」，而是检查**四个分项是否互不重叠、是否恰好覆盖全部题目**。
断言当场失败，暴露出重复计数。

### 根因（`js/exam.js` 的 `Exam.submit`，两处重叠）

| # | 重叠 | 原因 |
|---|---|---|
| 1 | `wrong` ∩ `unanswered` | 计分循环里「没答对」就 `wrong++`，而**未作答**也走这一支；结果对象又写成 `wrong: scored - correct`，把未作答一起算进「答错」。错题本逻辑本身是分开的（未作答不写错题本），只有**成绩数字**混了。 |
| 2 | `unanswered` ∩ `unverified` | 「未作答」在判分前就累加，**待核对/无答案**题（`Practice.judge` 返回 `correct === null`）也被算进未作答。逐题核账实测：100 题 → `unanswered 94`、`unverified 4`，而可判分未作答其实只有 90 题（94 = 90 + 4）。 |

### 修法

把四个分项改成**互斥且完备**的口径（`js/exam.js`）：

- 不可判分的题（待核对 / 无答案）→ **只**计入 `unverified`；
- 可判分且**未作答** → 计入 `unanswered`（章节表的 `blank` 同口径）；
- 可判分且**答错** → 计入 `wrong`；
- 可判分且答对 → 计入 `correct`。

于是恒等式成立：

```
correct + wrong + unanswered + unverified === total
correct + wrong + unanswered              === scored   （可判分题数，得分率的分母）
```

得分率算法**未改**（仍是 `正确 / 可判分题数`），所以交卷分数不变，只是分项不再自相矛盾。
`chapterRank()` 的章节正确率随之变为「答对 ÷ (答对+答错)」＝**已作答题**的正确率，
未作答单独以「未答」列展示，比原来「把空白当错」更符合直觉。

### 复验证据

`work/domtest/diag_exam.js`（逐题核账，与成绩对象对账）：

```
total = 100   scored = 97   correct = 3   wrong = 3   unanswered = 91   unverified = 3
correct+wrong+unanswered+unverified = 100 == total ✅
correct+wrong+unanswered            = 97  == scored ✅
scored+unverified                   = 100 == total ✅
逐题核账 buckets 合计 = 100 ✅
```

`work/domtest/test.js` 端到端：

```
考试交卷 OK：得分 4，总 100，正确 4，错误 2，未答 92，待核对 2
（4 + 2 + 92 + 2 = 100 ✅）
DOM 端到端测试全部通过 ✅   console 错误 0 / 警告 0
```

### 顺带修掉的测试脆弱性

同一个测试用例原本按题号硬点前 6 题的选项，而组卷池里含少量**待核对**题
（答案键可能越界、页面上没有对应按钮），于是会**随机少答一题**（实测出现 5/6），
表现为「测试失败」而非 APP 缺陷。已改为**只挑选项键确实存在的题**来点，
并断言「点击成功数 == 作答记录数」，消除这类随机失败。

---

## 二、Service Worker 未预缓存 8/9 份整理报告（2026-10-19 发现并修复）

### 症状

以 http 方式打开 APP 后，断网时「资料与设置」里的报告**打不开**：
`sw.js` 的 `ASSETS` 只列了应用外壳（html/css/js/data/icons），没列 `docs/*.md`。

### 修法

- `ASSETS` 补入 `docs/01..09`、`README.md`、`icons/icon.svg`（清单由 16 项增至 25 项）；
- 缓存版本 `ce-study-v4` → **`ce-study-v5`**，强制客户端刷新旧缓存。

### 复验证据

新增 `work/check_offline.py`（已并入 `finalize_all.py` 流水线），四道检查：

```
【1】外部依赖：✅ 没有任何外部 script/link/iframe/fetch 引用 —— 完全自包含
      （另有 32 处 http(s) 字样属“来源出处标注”，不发起请求）
【2】预缓存清单内路径：✅ 全部存在
【3】未预缓存文件：仅 start.cmd / start.ps1 / sw.js（本就无需缓存）✅
【4】报告：代码引用 9 份、磁盘 9 份、预缓存 9 份 ✅
结论: ✅ 完全自包含、可离线使用
```

> 说明：`data/knowledge.js` 里有 32 处 `http(s)` 是**核实来源链接**（企业事实、时政条目的出处），
> 以文本/可点击链接呈现，**不会在启动或运行中发起任何请求**，因此不影响离线使用。

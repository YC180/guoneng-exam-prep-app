/* 无浏览器冒烟测试：在 Node vm 中加载题库与核心模块，验证解析与关键逻辑。 */
'use strict';
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const APP = 'D:\\DOWNLOADS\\app';
const sandbox = {
  console,
  setTimeout, clearTimeout, setInterval, clearInterval,
  Date, Math, JSON, Object, Array, String, Number, Boolean, Promise, Error,
  parseInt, parseFloat, isNaN, RegExp,
};
sandbox.window = sandbox;
sandbox.globalThis = sandbox;
sandbox.localStorage = null;       // 强制回退内存后端
sandbox.indexedDB = undefined;
sandbox.navigator = {};
vm.createContext(sandbox);

function load(rel) {
  const p = path.join(APP, rel);
  const code = fs.readFileSync(p, 'utf8');
  vm.runInContext(code, sandbox, { filename: rel });
}

const t0 = Date.now();
load('data/questions.js');
load('data/knowledge.js');
console.log(`载入题库文件 ${Date.now() - t0} ms`);

const bankRaw = sandbox.window.CE_BANK;
if (!bankRaw) throw new Error('CE_BANK 未定义');
console.log(`内置题库：${bankRaw.questions.length} 题，生成于 ${bankRaw.generatedAt || '未知'}`);

['js/store.js', 'js/bank.js', 'js/practice.js', 'js/exam.js', 'js/stats.js'].forEach(load);

(async () => {
  await sandbox.Store.init();
  console.log(`存储后端：${sandbox.Store.backendName()}`);

  const info = await sandbox.Bank.load();
  console.log(`Bank.load -> 总计 ${info.total}（内置 ${info.builtin} / 导入 ${info.imported}）`);

  const Bank = sandbox.Bank;
  const Practice = sandbox.Practice;
  const Stats = sandbox.Stats;
  const Exam = sandbox.Exam;

  // --- 结构不变量 ---
  const bad = Bank.all.filter(q => !q.id || !q.stem || !Array.isArray(q.answer) || !Array.isArray(q.options));
  console.log(`结构异常题目：${bad.length}`);

  const noAns = Bank.all.filter(q => !q.answer.length).length;
  const needsRev = Bank.all.filter(q => q.answerStatus === 'needs_review').length;
  console.log(`无答案 ${noAns} 题，待核对 ${needsRev} 题`);

  const rep = Bank.validate();
  console.log(`Bank.validate -> 异常条目 ${rep.issueCount}，重复 ID ${rep.duplicateIds.length}`);
  console.log('  异常分布: ' + JSON.stringify(rep.byIssue));

  // --- 判分 ---
  const single = Bank.all.find(q => q.type === 'single_choice' && q.answer.length === 1 && q.answerStatus === 'verified');
  const multi = Bank.all.find(q => q.type === 'multiple_choice' && q.answer.length > 1 && q.answerStatus === 'verified');
  const fill = Bank.all.find(q => q.type === 'fill_blank' && q.answer.length);
  console.log(`判分抽样：单选 ${single ? single.id : '无'} / 多选 ${multi ? multi.id : '无'} / 填空 ${fill ? fill.id : '无'}`);

  if (single) {
    const ok = Practice.judge(single, [single.answer[0]]).correct;
    const wrongKey = (single.options.find(o => o.key !== single.answer[0]) || {}).key;
    const bad1 = Practice.judge(single, [wrongKey]).correct;
    console.log(`  单选：正确作答=${ok}（应为 true），干扰项=${bad1}（应为 false）`);
    if (ok !== true || bad1 !== false) throw new Error('单选判分错误');
  }
  if (multi) {
    const full = Practice.judge(multi, multi.answer.slice()).correct;
    const part = Practice.judge(multi, multi.answer.slice(0, 1)).correct;
    console.log(`  多选：全对=${full}（应为 true），漏选=${part}（应为 false）`);
    if (full !== true || part !== false) throw new Error('多选判分错误');
  }
  if (fill) {
    const f1 = Practice.judge(fill, [fill.answer[0]]).correct;
    console.log(`  填空：原文答案=${f1}（应为 true）`);
    if (f1 !== true) throw new Error('填空判分错误');
  }

  const unver = Bank.all.find(q => q.answerStatus === 'needs_review');
  if (unver) {
    const r = Practice.judge(unver, ['A']);
    console.log(`  待核对题目判分返回 correct=${r.correct}（应为 null，不计入统计）`);
    if (r.correct !== null) throw new Error('待核对题目被错误判分');
  }

  // --- 状态与练习 ---
  const state = {
    meta: { targetDate: '2026-10-24', settings: { fontScale: 1, dark: false, dailyNew: 0 } },
    progress: {}, wrongBook: {}, logs: {}, exams: [], session: null, currentExam: null,
  };

  const q = Bank.all[0];
  const r1 = Practice.answer(state, q, [q.answer[0]]);
  console.log(`作答一道题：判分=${r1.correct}，记录 seen=${state.progress[q.id].seen}`);

  for (let i = 0; i < 200; i++) {
    const qq = Bank.all[i];
    const wrongAns = qq.options.length > 1 ? [qq.options.find(o => o.key !== qq.answer[0]).key] : [];
    Practice.answer(state, qq, wrongAns);
  }
  console.log(`错题本：${Object.keys(state.wrongBook).length} 题（应为 200 左右）`);

  const plan = Practice.plan(state, '2026-10-24');
  console.log(`每日计划：剩余 ${plan.remainingDays} 天，未学 ${plan.unlearned}，每日新题 ${plan.perDayNew}，今日目标 ${plan.goal}`);

  const ov = Stats.overview(state);
  console.log(`统计：已答 ${ov.seen}，正确率 ${ov.accuracy === null ? '—' : (ov.accuracy * 100).toFixed(1) + '%'}，错题 ${ov.wrongQ}`);

  const tr = Stats.trend(state, 7);
  console.log(`趋势数组长度 ${tr.length}，今日答题 ${tr[tr.length - 1].answered}`);

  // --- 模拟考试 ---
  const exam = Exam.create(state, { count: 30, durationMin: 10, pool: Bank.all.filter(x => x.type === 'single_choice' && x.answerStatus === 'verified') });
  exam.qids.forEach((qid, i) => {
    const qq = Bank.byId[qid];
    exam.answers[qid] = i % 2 === 0 ? qq.answer.slice() : [qq.options.find(o => o.key !== qq.answer[0]).key];
  });
  const res = Exam.submit(state, exam);
  console.log(`模拟考：题量 ${res.total}，可判分 ${res.scored}，对 ${res.correct}，错 ${res.wrong}，得分 ${res.score}，待核对 ${res.unverified}`);
  if (res.correct !== 15) throw new Error(`预期答对 15 题，实际 ${res.correct}`);
  const rank = Exam.chapterRank(res);
  console.log(`章节分析 ${rank.length} 行，最弱：${rank[0] ? rank[0].chapter : '—'}`);

  // --- 筛选与搜索 ---
  const cats = Bank.facets.categories.slice(0, 6).map(c => `${c.name}(${c.count})`).join('，');
  console.log(`资料类别：${cats}`);
  const kw = Bank.all[5].stem.slice(0, 4);
  console.log(`关键词「${kw}」命中 ${Bank.filter({ keyword: kw }).length} 题`);
  console.log(`按类别+题型筛选（${Bank.facets.categories[0].name} / single_choice）：${Bank.filter({ category: Bank.facets.categories[0].name, type: 'single_choice' }).length} 题`);

  console.log('\n全部冒烟测试通过 ✅');
})().catch(e => { console.error('冒烟测试失败：', e); process.exit(1); });

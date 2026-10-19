/* 真实 DOM 测试：用 jsdom 加载 index.html 与全部脚本，逐个页面渲染并走通练习/考试流程。 */
'use strict';
const fs = require('fs');
const path = require('path');
const { JSDOM } = require('jsdom');

const APP = process.argv[2] || process.env.APPTEST_ROOT || 'D:\\DOWNLOADS\\app';
const SCRIPTS = [
  'data/questions.js', 'data/knowledge.js',
  'js/store.js', 'js/bank.js', 'js/practice.js', 'js/exam.js',
  'js/stats.js', 'js/io.js', 'js/ui.js', 'js/app.js',
];

const errors = [];
const warns = [];

function makeDom() {
  const html = fs.readFileSync(path.join(APP, 'index.html'), 'utf8');
  const dom = new JSDOM(html, {
    runScripts: 'outside-only',
    pretendToBeVisual: true,
    url: 'http://127.0.0.1:8777/index.html',
  });
  const w = dom.window;
  // 补齐 jsdom 未实现的浏览器 API
  w.scrollTo = () => {};
  w.confirm = () => true;
  w.alert = () => {};
  w.HTMLElement.prototype.scrollIntoView = () => {};
  if (!w.URL.createObjectURL) w.URL.createObjectURL = () => 'blob:stub';
  w.addEventListener('error', (e) => errors.push('window.error: ' + (e.error && e.error.stack || e.message)));
  w.onerror = (msg, src, line, col, err) => errors.push(`onerror: ${msg} @${line}:${col}\n${err && err.stack || ''}`);
  const origErr = w.console.error;
  w.console.error = (...a) => { errors.push('console.error: ' + a.map(String).join(' ')); };
  w.console.warn = (...a) => { warns.push('console.warn: ' + a.map(String).join(' ')); };
  w.console.log = () => {};
  return { dom, w };
}

function loadScripts(w) {
  for (const rel of SCRIPTS) {
    const code = fs.readFileSync(path.join(APP, rel), 'utf8');
    try {
      w.eval(code);
    } catch (e) {
      throw new Error(`加载 ${rel} 失败: ${e.message}\n${e.stack}`);
    }
  }
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function assert(cond, msg) {
  if (!cond) throw new Error('断言失败：' + msg);
}

function viewText(w) {
  const v = w.document.getElementById('view');
  return (v && v.textContent || '').replace(/\s+/g, ' ').trim();
}

function clickNav(w, go) {
  const btn = w.document.querySelector(`#nav button[data-go="${go}"]`);
  assert(btn, `找不到导航按钮 ${go}`);
  btn.click();
}

function act(w, action, selectorExtra) {
  const sel = `[data-act="${action}"]` + (selectorExtra || '');
  const el = w.document.querySelector(sel);
  assert(el, `找不到元素 ${sel}`);
  el.click();
  return el;
}

(async () => {
  const { w } = makeDom();
  loadScripts(w);

  // 等待 boot() 完成（Store.init -> Bank.load -> 首屏渲染）
  let waited = 0;
  while (!w.App || !w.App.ready) {
    await sleep(100);
    waited += 100;
    if (waited > 30000) throw new Error('App 启动超时（30s）');
  }
  console.log(`启动完成，用时约 ${waited} ms；存储后端 ${w.Store.backendName()}；题库 ${w.Bank.all.length} 题`);

  // ---- 首页 ----
  assert(w.App.view === 'home', '首屏应为 home，实际 ' + w.App.view);
  let t = viewText(w);
  assert(t.includes('距离学习完成目标'), '首页缺少倒计时');
  assert(t.includes('今日任务'), '首页缺少今日任务');
  assert(t.includes('学习总览'), '首页缺少学习总览');
  console.log('首页渲染 OK（' + t.length + ' 字符）');

  // ---- 七个页面逐个渲染 ----
  const pages = [
    ['bank', ['题库', '搜索题干']],
    ['practice', ['选择练习方式', '题量概览']],
    ['wrong', ['错题总数']],
    ['exam', ['创建试卷', '历史成绩']],
    ['stats', ['总体', '近 14 天趋势']],
    ['more', ['目标与偏好', '题库与数据', '已核实知识点', '使用说明', '备考报告']],
    ['home', ['今日任务']],
  ];
  for (const [go, needles] of pages) {
    clickNav(w, go);
    await sleep(30);
    const body = viewText(w);
    for (const n of needles) {
      assert(body.includes(n), `${go} 页面缺少「${n}」；实际内容片段：${body.slice(0, 160)}`);
    }
    console.log(`页面 ${go} OK（${body.length} 字符）`);
  }

  // ---- 题库筛选交互 ----
  clickNav(w, 'bank');
  await sleep(20);
  const kwInput = w.document.getElementById('bankKw');
  assert(kwInput, '题库页缺少搜索框');
  kwInput.value = '国家能源集团';
  kwInput.dispatchEvent(new w.Event('input', { bubbles: true }));
  await sleep(500);
  let bankTxt = viewText(w);
  const m = /共 (\d+) 题/.exec(bankTxt);
  assert(m && Number(m[1]) > 0, '搜索“国家能源集团”应命中题目，实际：' + (m ? m[1] : '无匹配数'));
  console.log(`搜索命中 ${m[1]} 题`);

  // 类别下拉
  const catSel = w.document.getElementById('bankCat');
  assert(catSel && catSel.options.length > 1, '类别下拉为空');
  catSel.value = catSel.options[1].value;
  catSel.dispatchEvent(new w.Event('change', { bubbles: true }));
  await sleep(60);
  assert(viewText(w).includes('共'), '切换类别后未渲染结果');
  console.log(`类别筛选「${catSel.value}」OK`);

  // 标签筛选（先重置，避免与类别筛选叠加成空结果）
  act(w, 'bank-reset');
  await sleep(60);
  const tagBtn = w.document.querySelector('[data-tag]');
  assert(tagBtn, '题库页没有标签筛选按钮');
  const tagName = tagBtn.getAttribute('data-tag');
  tagBtn.click();
  await sleep(60);
  let tagTxt = viewText(w);
  assert(tagTxt.includes('共'), '标签筛选后未渲染列表');
  const tagCount = (/共 (\d+) 题/.exec(tagTxt) || [])[1];
  assert(Number(tagCount) > 0, `标签「${tagName}」筛选结果为空`);
  console.log(`标签筛选「${tagName}」OK（${tagCount} 题）`);
  assert(w.document.querySelector('[data-open-q]'), '标签筛选后列表无题目项');

  // 再重置回全库，供后续步骤使用
  act(w, 'bank-reset');
  await sleep(60);
  assert(viewText(w).includes('全部资料类别'), '重置筛选未生效');
  console.log('重置筛选 OK');

  // ---- 打开单题详情 ----
  const qitem = w.document.querySelector('[data-open-q]');
  assert(qitem, '题库列表没有题目项');
  const openedId = qitem.getAttribute('data-open-q');
  qitem.click();
  await sleep(40);
  assert(w.App.view === 'question', '应进入题目详情页');
  let qt = viewText(w);
  assert(qt.includes('来源：'), '题目详情缺少来源标注');
  assert(qt.includes('解析') || qt.includes('原资料未提供解析'), '题目详情缺少解析区');
  assert(qt.includes('历史记录'), '题目详情缺少历史记录');
  console.log(`题目详情 ${openedId} OK`);

  // 收藏与掌握度
  act(w, 'fav');
  await sleep(40);
  assert(w.Practice.rec(w.App.state.progress, openedId).fav === true, '收藏未生效');
  act(w, 'mastery', '[data-level="known"]');
  await sleep(40);
  assert(w.Practice.rec(w.App.state.progress, openedId).mastery === 'known', '掌握度未生效');
  console.log('收藏 / 掌握度标记 OK');

  // ---- 练习流程：开始 → 选选项 → 提交 → 下一题 ----
  clickNav(w, 'practice');
  await sleep(30);
  act(w, 'p-start');
  await sleep(60);
  assert(w.App.state.session && w.App.state.session.queue.length, '练习会话未创建');
  const qlen = w.App.state.session.queue.length;
  console.log(`练习会话已创建：${qlen} 题（模式 ${w.App.state.session.mode}）`);

  const firstQid = w.App.state.session.queue[0];
  const firstQ = w.Bank.byId[firstQid];
  let optBtn = w.document.querySelector('[data-opt]');
  assert(optBtn, '练习页没有选项按钮');
  optBtn.click();
  await sleep(30);
  const chosen = optBtn.getAttribute('data-opt');
  assert((w.App.state.session.ua[firstQid] || []).includes(chosen), '选项点击未写入会话状态');
  console.log(`已选择选项 ${chosen}（题型 ${firstQ.type}）`);

  act(w, 'p-submit');
  await sleep(60);
  let pTxt = viewText(w);
  assert(w.App.state.session.submitted[firstQid], '提交后未标记已作答');
  assert(/回答正确|回答错误|待核对|原资料未提供标准答案|请对照参考答案自评|无法自动判分/.test(pTxt),
    '提交后未显示判分反馈；实际：' + pTxt.slice(0, 220));
  const rec = w.Practice.rec(w.App.state.progress, firstQid);
  assert(rec.seen >= 1, '作答未写入学习记录');
  console.log(`判分反馈 OK（seen=${rec.seen}, 对=${rec.correctCount}, 错=${rec.wrongCount}）`);

  act(w, 'p-next');
  await sleep(40);
  assert(w.App.state.session.idx === 1, '下一题未前进');
  console.log('下一题 OK');

  // 手动答错 → 进错题本
  const secondQid = w.App.state.session.queue[1];
  const secondQ = w.Bank.byId[secondQid];
  if (secondQ.options && secondQ.options.length) {
    const wrongOpt = secondQ.options.find((o) => !(secondQ.answer || []).map(String).includes(o.key));
    if (wrongOpt) {
      const btn = w.document.querySelector(`[data-opt="${wrongOpt.key}"]`);
      if (btn) { btn.click(); await sleep(20); act(w, 'p-submit'); await sleep(50); }
      const wbCount = Object.keys(w.App.state.wrongBook).length;
      console.log(`答错后错题本 ${wbCount} 题`);
    }
  }

  // ---- 模拟考：组卷 → 答题 → 交卷 → 成绩/回顾 ----
  clickNav(w, 'exam');
  await sleep(30);
  const eCount = w.document.getElementById('eCount');
  eCount.value = '10';
  act(w, 'e-start');
  await sleep(80);
  assert(w.App.state.currentExam, '未创建考试');
  const exam = w.App.state.currentExam;
  assert(exam.qids.length === 10, `考试题量应为 10，实际 ${exam.qids.length}`);
  console.log(`考试已创建：${exam.qids.length} 题 / ${exam.durationMin} 分钟`);

  // 答 6 道**可作答**题（前 3 题按其正确答案、随后 3 题故意选错）。
  // 注意：组卷池里含少量「待核对 / 无答案」题（交卷时计入 unverified、不计成绩），
  // 它们的答案键可能越界，题干里未必有对应按钮。若不加筛选，测试会因
  // “点了不存在的选项”而随机少答一题（曾实测出现 5/6），属于**测试脆弱**而非 APP 缺陷。
  // 因此这里只挑“选项键确实存在”的题来点，其余跳过（保持未作答）。
  let correctPlanned = 0;
  let clicked = 0;
  const NEED = 6;
  for (let i = 0; i < Math.min(exam.qids.length, NEED * 4) && clicked < NEED; i++) {
    const qid = exam.qids[i];
    const q = w.Bank.byId[qid] || {};
    const keys = (q.options || []).map((o) => String(o.key));
    let key = null;
    if (clicked < 3 && (q.answer || []).length && keys.indexOf(String(q.answer[0])) >= 0) {
      key = String(q.answer[0]);          // 可判分题：按正确答案点，制造“答对”
      correctPlanned++;
    } else if (keys.length) {
      const bad = (q.options || []).find((o) => (q.answer || []).map(String).indexOf(o.key) < 0);
      if (bad) key = bad.key;             // 故意答错
    }
    if (key) {
      const btn = w.document.querySelector(`[data-opt="${key}"]`);
      if (btn) { btn.click(); clicked++; }
    }
    await sleep(15);
    const nextBtn = w.document.querySelector('[data-act="e-next"]');
    if (nextBtn && !nextBtn.disabled) nextBtn.click();
    await sleep(15);
  }
  const answered = Object.keys(exam.answers).filter((k) => exam.answers[k] && exam.answers[k].length).length;
  console.log(`已答 ${answered} 题（点击成功 ${clicked}，计划答对 ${correctPlanned} 题）`);
  assert(clicked === NEED, `应能点到 ${NEED} 道可作答题的选项，实际点到 ${clicked}`);
  assert(answered === clicked, `作答记录数应与点击成功数一致：${answered} vs ${clicked}`);

  // 答题卡
  act(w, 'e-card');
  await sleep(30);
  assert(w.document.querySelector('.anscard button'), '答题卡未渲染');
  console.log('答题卡 OK');

  // 标记待查
  act(w, 'e-flag');
  await sleep(20);
  assert(Object.keys(exam.flagged).length > 0, '标记待查未生效');

  // 交卷
  act(w, 'e-submit');
  await sleep(120);
  assert(w.App.state.examResult, '交卷后没有成绩');
  const res = w.App.state.examResult.result;
  let et = viewText(w);
  assert(et.includes('成绩') && et.includes('章节分析') && et.includes('题目回顾'),
    '成绩页缺少板块；实际：' + et.slice(0, 200));
  console.log(`成绩页 OK：题量 ${res.total}，可判分 ${res.scored}，对 ${res.correct}，错 ${res.wrong}，得分 ${res.score}，待核对 ${res.unverified}`);
  assert(res.total === 10, '成绩单题量应为 10');
  assert(res.scored + res.unverified + 0 === res.total || res.scored + res.unverified === res.total,
    `可判分 ${res.scored} + 待核对 ${res.unverified} 应等于总题量 ${res.total}`);

  // ---- 统计页应反映刚才的作答 ----
  clickNav(w, 'stats');
  await sleep(40);
  const statsTxt = viewText(w);
  assert(statsTxt.includes('覆盖率') || statsTxt.includes('正确率'), '统计页缺少指标');
  const ov = w.Stats.overview(w.App.state);
  assert(ov.seen > 0, '统计的已答题数应大于 0');
  console.log(`统计页 OK：已答 ${ov.seen} 题，覆盖率 ${(ov.coverage * 100).toFixed(1)}%，正确率 ${ov.accuracy === null ? '—' : (ov.accuracy * 100).toFixed(1) + '%'}`);

  // ---- 错题本页面 ----
  clickNav(w, 'wrong');
  await sleep(30);
  console.log('错题本 OK（' + Object.keys(w.App.state.wrongBook).length + ' 题）');

  // ---- 设置：改目标日期 + 深色 + 字号 ----
  clickNav(w, 'more');
  await sleep(30);
  const dt = w.document.getElementById('setTarget');
  dt.value = '2026-10-24';
  const daily = w.document.getElementById('setDailyNew');
  daily.value = '60';
  const dark = w.document.getElementById('setDark');
  dark.checked = true;
  const font = w.document.getElementById('setFont');
  font.value = '1.12';
  act(w, 'save-settings');
  await sleep(120);
  assert(w.App.state.meta.settings.dailyNew === 60, '每日上限未保存');
  assert(w.document.documentElement.getAttribute('data-theme') === 'dark', '深色模式未应用');
  console.log('设置保存 OK（每日 60 题 / 深色 / 字号 1.12）');

  // 每日计划应受上限约束
  const plan = w.Practice.plan(w.App.state, '2026-10-24');
  assert(plan.perDayNew <= 60, `每日新题应受上限 60 约束，实际 ${plan.perDayNew}`);
  console.log(`每日计划 OK：剩余 ${plan.remainingDays} 天，每日新题 ${plan.perDayNew}，今日目标 ${plan.goal}`);

  // ---- 校验功能 ----
  act(w, 'validate');
  await sleep(120);
  const impPreview = w.document.getElementById('impPreview');
  assert(impPreview && impPreview.textContent.includes('校验结果'), '校验结果未渲染');
  console.log('题库校验渲染 OK');

  // ---- 主题切换按钮 ----
  w.document.getElementById('btnTheme').click();
  await sleep(30);
  assert(w.document.documentElement.getAttribute('data-theme') === 'light', '主题切换未生效');
  console.log('主题切换 OK');

  // ---- 持久化：重新读回 ----
  const persisted = await w.Store.get('progress', null);
  assert(persisted && Object.keys(persisted).length > 0, '学习进度未持久化');
  const persistedMeta = await w.Store.get('meta', null);
  assert(persistedMeta && persistedMeta.targetDate, 'meta 未持久化');
  console.log(`持久化 OK：progress ${Object.keys(persisted).length} 条，meta.targetDate=${persistedMeta.targetDate}`);

  // ---- 模拟考试：二次流程 + 成绩分项自洽 + 记录持久化 ----
  // （前面的用例已跑过一次考试，这里先回到设置页，再验一遍并做分项求和校验）
  clickNav(w, 'exam');
  await sleep(60);
  if (w.App.state.examResult) { act(w, 'e-again'); await sleep(100); }
  assert(w.App.view === 'exam', '未进入考试页');
  act(w, 'e-start');
  await sleep(200);
  const ex = w.App.state.currentExam;
  assert(ex && ex.qids && ex.qids.length > 0, '考试未成功开始');
  console.log(`模拟考试开始 OK：${ex.qids.length} 题，时限 ${ex.durationMin} 分钟，范围「${ex.scope}」`);

  // 作答前若干题（选第一个选项），并逐题前进
  const nAns = Math.min(6, ex.qids.length);
  for (let i = 0; i < nAns; i++) {
    const opt = w.document.querySelector('#view [data-opt]');
    if (opt) opt.click();
    await sleep(40);
    const nx = w.document.querySelector('#view [data-act="e-next"]');
    if (nx) nx.click();
    await sleep(40);
  }
  const examAnswered = Object.keys(w.App.state.currentExam.answers || {}).length;
  assert(examAnswered > 0, '考试作答未记录');
  console.log(`考试作答 OK：已记录 ${examAnswered} 题`);

  // 交卷（confirm 需放行）
  w.confirm = function () { return true; };
  act(w, 'e-submit');
  await sleep(300);
  const er = w.App.state.examResult;
  assert(er && er.result, '交卷后未生成成绩对象');
  assert(w.App.state.currentExam === null || w.App.state.currentExam === undefined,
    '交卷后应清空进行中的考试');
  const r = er.result;
  assert(typeof r.score === 'number' && r.total > 0, '成绩字段不完整');
  assert(r.correct + r.wrong + r.unanswered + r.unverified === r.total,
    `成绩分项之和应等于总题数：${r.correct}+${r.wrong}+${r.unanswered}+${r.unverified} != ${r.total}`);
  console.log(`考试交卷 OK：得分 ${r.score}，总 ${r.total}，正确 ${r.correct}，错误 ${r.wrong}，` +
    `未答 ${r.unanswered}，待核对 ${r.unverified}`);
  // 成绩页应渲染出来
  const resTxt = viewText(w);
  assert(/得分|正确/.test(resTxt), '成绩页未渲染');
  // 考试记录应持久化到 exams
  assert(Array.isArray(w.App.state.exams) && w.App.state.exams.length > 0, '考试记录未保存');
  console.log(`考试记录持久化 OK：${w.App.state.exams.length} 次`);

  // ---- 待核对题不得污染正确率 / 错题本（与成绩页同一口径，大纲 5.3）----
  const unvQ = w.Bank.all.find((q) => q.answerStatus !== 'verified' && q.type === 'single_choice' &&
    (q.options || []).length);
  assert(unvQ, '题库里应有待核对题用于本项校验');
  const recBefore = w.Practice.rec(w.App.state.progress, unvQ.id);
  const bW = recBefore.wrongCount || 0, bC = recBefore.correctCount || 0, bU = recBefore.unverified || 0;
  const wbBefore = Object.keys(w.App.state.wrongBook).length;
  w.Practice.answer(w.App.state, unvQ, [String((unvQ.options[0] || {}).key || 'A')], { silent: false });
  const recAfter = w.Practice.rec(w.App.state.progress, unvQ.id);
  assert((recAfter.wrongCount || 0) === bW, `待核对题被计成答错：${bW} → ${recAfter.wrongCount}`);
  assert((recAfter.correctCount || 0) === bC, `待核对题被计成答对：${bC} → ${recAfter.correctCount}`);
  assert((recAfter.unverified || 0) === bU + 1, `待核对题未计入 unverified：${bU} → ${recAfter.unverified}`);
  assert(Object.keys(w.App.state.wrongBook).length === wbBefore,
    '待核对题污染了错题本');
  console.log(`待核对题口径 OK：unverified ${bU} → ${recAfter.unverified}，未计正确/错误、未进错题本`);

  // ---- 统计正确率的分母只应含“可判分题”（正确的公式，而非被待核对题稀释）----
  const allRec = Object.keys(w.App.state.progress).map((k) => w.App.state.progress[k]);
  const sumC = allRec.reduce((a, r) => a + (r.correctCount || 0), 0);
  const sumW = allRec.reduce((a, r) => a + (r.wrongCount || 0), 0);
  const ovA = w.Stats.overview(w.App.state);
  const expect = (sumC + sumW) ? sumC / (sumC + sumW) : null;
  assert((ovA.accuracy === null) === (expect === null),
    '正确率是否为空与可判分题数不一致');
  if (expect !== null) {
    assert(Math.abs(ovA.accuracy - expect) < 1e-9,
      `正确率应=可判分题正确率：页面 ${ovA.accuracy} vs 期望 ${expect}`);
  }
  console.log(`正确率口径 OK：${sumC}/${sumC + sumW} = ${(expect * 100).toFixed(1)}%（待核对题未计入分母）`);

  // ---- 导出功能应存在（离线可用，不依赖网络）----
  assert(typeof w.IO.exportProgress === 'function' &&
    typeof w.IO.exportBank === 'function' &&
    typeof w.IO.exportBackup === 'function', '导出接口缺失');
  console.log('导出接口 OK（学习记录 / 题库 / 完整备份）');

  // ---- 汇总 ----
  const realErrors = errors.filter((e) => !/Not implemented|Could not parse CSS|cssom/i.test(e));
  console.log('\n---- 结果 ----');
  console.log(`页面渲染与交互：全部通过`);
  console.log(`console 错误：${realErrors.length}`);
  realErrors.slice(0, 15).forEach((e) => console.log('  ! ' + e.slice(0, 300)));
  console.log(`console 警告：${warns.length}`);
  if (realErrors.length) {
    console.log('\n存在错误 ❌');
    process.exit(1);
  }
  console.log('\nDOM 端到端测试全部通过 ✅');
  process.exit(0);
})().catch((e) => {
  console.error('\nDOM 测试失败 ❌\n' + (e.stack || e.message));
  if (errors.length) {
    console.error('\n捕获到的页面错误：');
    errors.slice(0, 20).forEach((x) => console.error('  ! ' + x.slice(0, 400)));
  }
  process.exit(1);
});

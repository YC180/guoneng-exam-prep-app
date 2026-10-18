/* 诊断：交卷成绩各项计数是否自洽（不重叠、总和等于总题数）。
   背景：成绩页曾出现「答错 94 / 未作答 94」并存；修掉 wrong 的重叠后，
   仍发现 correct+wrong+unanswered+unverified 与 total 不符，需要逐题核账。 */
'use strict';
const fs = require('fs');
const path = require('path');
const { JSDOM } = require('jsdom');

const APP = 'D:\\DOWNLOADS\\app';
const SCRIPTS = [
  'data/questions.js', 'data/knowledge.js',
  'js/store.js', 'js/bank.js', 'js/practice.js', 'js/exam.js',
  'js/stats.js', 'js/io.js', 'js/ui.js', 'js/app.js',
];
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

(async () => {
  const dom = new JSDOM(fs.readFileSync(path.join(APP, 'index.html'), 'utf8'), {
    runScripts: 'outside-only', pretendToBeVisual: true,
    url: 'http://127.0.0.1:8777/index.html',
  });
  const w = dom.window;
  w.scrollTo = () => {}; w.confirm = () => true; w.alert = () => {};
  w.HTMLElement.prototype.scrollIntoView = () => {};
  if (!w.URL.createObjectURL) w.URL.createObjectURL = () => 'blob:stub';
  w.console.log = () => {};
  for (const rel of SCRIPTS) w.eval(fs.readFileSync(path.join(APP, rel), 'utf8'));

  await sleep(200);

  // 造一份考试：100 题
  const pool = w.Bank.filter({}).filter((q) =>
    q.type === 'single_choice' || q.type === 'multiple_choice' || q.type === 'true_false');
  console.log('候选池:', pool.length);
  const exam = w.Exam.create(w.App.state, { count: 100, durationMin: 60, pool: pool, scope: '诊断' });
  w.App.state.currentExam = exam;

  // 作答 6 题（前 3 题按正确答案、后 3 题故意错），其余留空
  let clickable = 0;
  for (let i = 0; i < exam.qids.length && clickable < 6; i++) {
    const q = w.Bank.byId[exam.qids[i]];
    if (!q) continue;
    const keys = (q.options || []).map((o) => String(o.key));
    let key = null;
    if (clickable < 3 && (q.answer || []).length && keys.indexOf(String(q.answer[0])) >= 0) key = String(q.answer[0]);
    else {
      const bad = (q.options || []).find((o) => (q.answer || []).map(String).indexOf(o.key) < 0);
      if (bad) key = bad.key;
    }
    if (key && keys.indexOf(String(key)) >= 0) { exam.answers[exam.qids[i]] = [String(key)]; clickable++; }
  }
  console.log('实际作答:', clickable, '题');

  const res = w.Exam.submit(w.App.state, exam);   // submit 直接返回 result
  console.log('\n--- 成绩对象 ---');
  console.log('total     =', res.total);
  console.log('scored    =', res.scored);
  console.log('correct   =', res.correct);
  console.log('wrong     =', res.wrong);
  console.log('unanswered=', res.unanswered);
  console.log('unverified=', res.unverified);
  console.log('score     =', res.score);

  const sum4 = res.correct + res.wrong + res.unanswered + res.unverified;
  console.log('\ncorrect+wrong+unanswered+unverified =', sum4, sum4 === res.total ? '== total ✅' : '!= total ❌');
  console.log('correct+wrong+unanswered            =', res.correct + res.wrong + res.unanswered,
    'vs scored', res.scored);
  console.log('scored+unverified                   =', res.scored + res.unverified,
    res.scored + res.unverified === res.total ? '== total ✅' : '!= total ❌');

  // 逐题核账：谁被计入了哪些桶
  const buckets = { correct: 0, wrong: 0, blank: 0, unver: 0, notfound: 0, other: 0 };
  const unverDetail = [];
  exam.qids.forEach((qid) => {
    const q = w.Bank.byId[qid];
    if (!q) { buckets.notfound++; return; }
    const ua = exam.answers[qid] || [];
    const jr = w.Practice.judge(q, ua);
    if (jr.correct === null) {
      buckets.unver++;
      if (ua.length) unverDetail.push(qid + '（已作答却是待核对）');
    } else if (jr.correct) buckets.correct++;
    else if (ua.length) buckets.wrong++;
    else buckets.blank++;
  });
  console.log('\n--- 逐题核账 ---');
  console.log(buckets);
  console.log('buckets 合计:', Object.values(buckets).reduce((a, b) => a + b, 0));
  if (unverDetail.length) console.log('待核对中“已作答”的题数:', unverDetail.length, unverDetail.slice(0, 3));
  process.exit(0);
})();

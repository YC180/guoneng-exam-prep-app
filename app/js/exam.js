/* 模拟考试引擎：组卷、倒计时、答题卡、交卷判分、成绩分析与题目回顾。 */
(function () {
  'use strict';

  var Exam = {
    /** 组卷 */
    create: function (state, opts) {
      opts = opts || {};
      var pool = opts.pool && opts.pool.length ? opts.pool : Bank.all.filter(function (q) {
        return q.type === 'single_choice' || q.type === 'multiple_choice' || q.type === 'true_false';
      });
      var list = pool.slice();
      if (opts.shuffle !== false) Bank.shuffle(list);
      var n = Math.min(opts.count || 100, list.length);
      list = list.slice(0, n);
      var exam = {
        id: 'exam-' + Date.now(),
        title: opts.title || ('模拟考试 ' + new Date().toLocaleString('zh-CN')),
        qids: list.map(function (q) { return q.id; }),
        durationMin: opts.durationMin || 60,
        startedAt: Date.now(),
        submitted: false,
        answers: {},
        flagged: {},
        showAnswerPerQuestion: !!opts.showAnswerPerQuestion,
        scope: opts.scope || '全部题库',
      };
      state.currentExam = exam;
      return exam;
    },

    /** 交卷判分 */
    submit: function (state, exam) {
      var scored = 0, correct = 0, wrong = 0, unverified = 0, unanswered = 0;
      var perChapter = {};
      var detail = [];
      exam.qids.forEach(function (qid) {
        var q = Bank.byId[qid];
        if (!q) return;
        var ua = exam.answers[qid] || [];
        var answered = ua.length > 0;
        var res = Practice.judge(q, ua);
        var judgeable = res.correct !== null;   /* 答案可靠、可判分（待核对/无答案题不可判分） */
        var ch = q.chapter || '未分类';
        perChapter[ch] = perChapter[ch] || { total: 0, correct: 0, wrong: 0, unverified: 0, blank: 0 };
        perChapter[ch].total++;
        /* 四个分项必须**互不重叠**，否则成绩页会出现自相矛盾的数字
           （曾实测：100 题里出现「答错 94 / 未作答 94」；改正后又发现
             「未作答」把「待核对」题也算了进去，导致四项之和 104 > 100）。
           口径：不可判分的题一律只算 unverified；只有**可判分且未作答**才算 unanswered。 */
        if (!judgeable) {
          unverified++;
          perChapter[ch].unverified++;
        } else {
          scored++;
          if (res.correct) { correct++; perChapter[ch].correct++; }
          else if (answered) { wrong++; perChapter[ch].wrong++; }
          else { unanswered++; perChapter[ch].blank++; }
        }
        detail.push({
          qid: qid, userAnswer: ua, answer: q.answer || [],
          correct: res.correct, answered: answered, chapter: ch, type: q.type,
        });
      });
      exam.submitted = true;
      exam.submittedAt = Date.now();
      exam.result = {
        total: exam.qids.length, scored: scored, correct: correct,
        /* 四个分项**互不重叠**，满足 correct + wrong + unanswered + unverified === total；
           scored（可判分题数）仍等于 correct + wrong + unanswered，得分率按其计算。 */
        wrong: wrong, unverified: unverified, unanswered: unanswered,
        score: scored ? Math.round(correct / scored * 100) : 0,
        elapsedSec: Math.round((exam.submittedAt - exam.startedAt) / 1000),
        perChapter: perChapter, detail: detail,
      };
      /* 把已作答的题目写入学习记录与错题本；
         未作答的题目只计入本次成绩（不得当作“答错”污染错题本）。 */
      detail.forEach(function (d) {
        if (!d.userAnswer || !d.userAnswer.length) return;
        var q = Bank.byId[d.qid];
        if (!q) return;
        Practice.answer(state, q, d.userAnswer, { silent: false });
      });
      state.currentExam = null;
      state.exams = state.exams || [];
      state.exams.unshift({
        id: exam.id, title: exam.title, createdAt: exam.startedAt,
        submittedAt: exam.submittedAt, scope: exam.scope,
        durationMin: exam.durationMin, qids: exam.qids, answers: exam.answers,
        result: exam.result,
      });
      if (state.exams.length > 60) state.exams.length = 60;
      return exam.result;
    },

    /** 剩余秒数 */
    remaining: function (exam, now) {
      if (!exam) return 0;
      var used = ((now || Date.now()) - exam.startedAt) / 1000;
      return Math.max(0, Math.round(exam.durationMin * 60 - used));
    },

    fmt: function (sec) {
      sec = Math.max(0, Math.round(sec));
      var h = Math.floor(sec / 3600), m = Math.floor((sec % 3600) / 60), s = sec % 60;
      function p(n) { return n < 10 ? '0' + n : '' + n; }
      return (h > 0 ? p(h) + ':' : '') + p(m) + ':' + p(s);
    },

    chapterRank: function (result) {
      var rows = [];
      Object.keys(result.perChapter || {}).forEach(function (ch) {
        var c = result.perChapter[ch];
        var denom = c.correct + c.wrong;
        rows.push({
          chapter: ch, total: c.total, correct: c.correct, wrong: c.wrong,
          unverified: c.unverified, blank: c.blank || 0,
          rate: denom ? c.correct / denom : null,
        });
      });
      rows.sort(function (a, b) {
        var ra = a.rate === null ? 2 : a.rate, rb = b.rate === null ? 2 : b.rate;
        return ra - rb;
      });
      return rows;
    },
  };

  window.Exam = Exam;
})();

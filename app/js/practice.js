/* 练习引擎：判分、学习记录、错题本、掌握程度、间隔复习、每日计划。 */
(function () {
  'use strict';

  var DAY = 86400000;

  /* 判分规则（对应大纲 5.4） */
  function normalizeText(s) {
    return String(s == null ? '' : s)
      .replace(/[\uFF01-\uFF5E]/g, function (c) {           /* 全角→半角 */
        return String.fromCharCode(c.charCodeAt(0) - 0xFEE0);
      })
      .replace(/\u3000/g, ' ')
      .replace(/\s+/g, '')
      .replace(/[，。、；：？！,.;:?!""''（）()【】\[\]]/g, '')
      .toLowerCase();
  }

  var Practice = {
    DAY: DAY,

    /* ------------------------------------------------------------ 判分 */
    judge: function (q, userAnswer) {
      var ans = (q.answer || []).map(function (x) { return String(x).toUpperCase(); });
      var type = q.type;
      if (q.answerStatus && q.answerStatus !== 'verified') {
        return { correct: null, reason: 'answer-unverified', expected: ans };
      }
      if (!ans.length) return { correct: null, reason: 'no-answer', expected: [] };

      if (type === 'single_choice') {
        var u1 = (userAnswer || []).map(function (x) { return String(x).toUpperCase(); });
        return { correct: u1.length === 1 && u1[0] === ans[0], expected: ans };
      }
      if (type === 'multiple_choice') {
        var u2 = (userAnswer || []).map(function (x) { return String(x).toUpperCase(); }).sort();
        var a2 = ans.slice().sort();
        return {
          correct: u2.length === a2.length && u2.every(function (x, i) { return x === a2[i]; }),
          expected: ans,
        };
      }
      if (type === 'true_false') {
        var u3 = normalizeText((userAnswer || [])[0]);
        var a3 = normalizeText(ans[0]);
        var map = { '正确': 'true', '对': 'true', '√': 'true', '是': 'true', 't': 'true', 'true': 'true',
                    '错误': 'false', '错': 'false', '×': 'false', '否': 'false', 'f': 'false', 'false': 'false' };
        return { correct: map[u3] && map[a3] && map[u3] === map[a3], expected: ans };
      }
      if (type === 'fill_blank') {
        var u4 = normalizeText((userAnswer || [])[0]);
        var hit = ans.some(function (a) {
          var na = normalizeText(a);
          return na && (u4 === na || (na.length > 2 && u4.indexOf(na) >= 0));
        });
        return { correct: hit, expected: ans };
      }
      return { correct: null, reason: 'self-assess', expected: ans };
    },

    /* -------------------------------------------------- 学习记录（进度） */
    defaultRec: function () {
      return {
        seen: 0, correctCount: 0, wrongCount: 0, lastResult: null, lastAt: 0,
        mastery: 'unknown', wrongReason: '', fav: false, reviewDue: 0, box: 0,
        streakCorrect: 0, selfScore: null,
      };
    },

    rec: function (progress, qid) {
      if (!progress[qid]) progress[qid] = Practice.defaultRec();
      return progress[qid];
    },

    /** 记录一次作答；返回判分结果 */
    answer: function (state, q, userAnswer, opts) {
      opts = opts || {};
      var res = Practice.judge(q, userAnswer);
      var progress = state.progress;
      var r = Practice.rec(progress, q.id);
      var now = Date.now();
      r.seen += 1;
      r.lastAt = now;
      r.lastResult = res.correct;
      r.lastAnswer = userAnswer;
      state.progress[q.id] = r;

      if (res.correct === true) {
        r.correctCount += 1;
        r.streakCorrect = (r.streakCorrect || 0) + 1;
        r.box = Math.min((r.box || 0) + 1, 6);
        r.reviewDue = now + intervalOf(r.box);
      } else if (res.correct === false) {
        r.wrongCount += 1;
        r.streakCorrect = 0;
        r.box = 0;
        r.reviewDue = now + DAY;                 /* 次日必复习 */
        if (!opts.silent) state.wrongBook[q.id] = (state.wrongBook[q.id] || 0) + 1;
      } else {
        /* 待核对 / 自评题：不纳入正确率统计（大纲 5.3） */
        r.unverified = (r.unverified || 0) + 1;
      }
      Practice.logStudy(state, res.correct === true, res.correct === false);
      return res;
    },

    logStudy: function (state, ok, bad) {
      var d = Practice.todayKey();
      state.logs[d] = state.logs[d] || { answered: 0, correct: 0, wrong: 0, newLearned: 0, minutes: 0 };
      state.logs[d].answered += 1;
      if (ok) state.logs[d].correct += 1;
      if (bad) state.logs[d].wrong += 1;
      state.logs[d].minutes = state.logs[d].minutes || 0;
    },

    addMinutes: function (state, minutes) {
      var d = Practice.todayKey();
      state.logs[d] = state.logs[d] || { answered: 0, correct: 0, wrong: 0, newLearned: 0, minutes: 0 };
      state.logs[d].minutes += minutes;
    },

    todayKey: function (ts) {
      var d = new Date(ts || Date.now());
      return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate());
    },

    setMastery: function (state, qid, level) {
      var r = Practice.rec(state.progress, qid);
      r.mastery = level;
      r.masteryAt = Date.now();
      if (level === 'known') r.reviewDue = Date.now() + 7 * DAY;
      if (level === 'vague') r.reviewDue = Date.now() + 2 * DAY;
      if (level === 'unknown') r.reviewDue = Date.now() + DAY;
    },

    toggleFav: function (state, qid) {
      var r = Practice.rec(state.progress, qid);
      r.fav = !r.fav;
      return r.fav;
    },

    setWrongReason: function (state, qid, reason) {
      var r = Practice.rec(state.progress, qid);
      r.wrongReason = reason || '';
    },

    /** 从错题本移除（用户确认已掌握） */
    removeWrong: function (state, qid) {
      delete state.wrongBook[qid];
      var r = Practice.rec(state.progress, qid);
      r.wrongCount = 0;
      r.mastery = 'known';
      r.reviewDue = Date.now() + 7 * DAY;
    },

    /* ---------------------------------------------------------- 各种题池 */
    poolNew: function (state) {
      return Bank.all.filter(function (q) { return !Practice.rec(state.progress, q.id).seen; });
    },
    poolWrong: function (state) {
      var wb = state.wrongBook || {};
      return Object.keys(wb).map(function (id) { return Bank.byId[id]; })
        .filter(Boolean)
        .sort(function (a, b) { return (wb[b.id] || 0) - (wb[a.id] || 0); });
    },
    poolFav: function (state) {
      return Bank.all.filter(function (q) { return Practice.rec(state.progress, q.id).fav; });
    },
    poolDue: function (state, ts) {
      var now = ts || Date.now();
      return Bank.all.filter(function (q) {
        var r = Practice.rec(state.progress, q.id);
        return r.seen && r.reviewDue && r.reviewDue <= now;
      });
    },
    poolWeak: function (state, minSeen) {
      return Bank.all.filter(function (q) {
        var r = Practice.rec(state.progress, q.id);
        var t = r.correctCount + r.wrongCount;
        return t >= (minSeen || 1) && r.wrongCount > 0 && r.correctCount / t < 0.6;
      });
    },

    /* -------------------------------------------------------- 每日计划 */
    plan: function (state, targetDate) {
      var remainingDays = Practice.daysLeft(targetDate);
      var total = Bank.all.length;
      var progress = state.progress;
      var learned = 0, mastered = 0, wrong = 0, fav = 0;
      Bank.all.forEach(function (q) {
        var r = progress[q.id];
        if (!r) return;
        if (r.seen) learned++;
        if (r.mastery === 'known') mastered++;
        if (r.fav) fav++;
      });
      wrong = Object.keys(state.wrongBook || {}).length;
      var unlearned = total - learned;
      var due = Practice.poolDue(state).length;

      /* 设置存放在 state.meta.settings（兼容旧结构 state.settings） */
      var settings = (state.meta && state.meta.settings) || state.settings || {};
      var dailyNewCap = settings.dailyNew || 0;
      var perDay = remainingDays > 0 ? Math.ceil(unlearned / remainingDays) : unlearned;
      if (dailyNewCap > 0) perDay = Math.min(perDay, dailyNewCap);
      var today = state.logs[Practice.todayKey()] || { answered: 0, correct: 0, wrong: 0 };
      /* 今日“新题”完成量按今日总答题量近似（无逐题日期时的简化口径） */
      var goalNew = perDay;
      var goalReview = due;
      var goal = goalNew + goalReview;
      var done = Math.min(today.answered, goal);
      return {
        remainingDays: remainingDays, total: total, learned: learned, unlearned: unlearned,
        mastered: mastered, wrong: wrong, fav: fav, due: due,
        goalNew: goalNew, goalReview: goalReview, goal: goal, done: done,
        todayAnswered: today.answered, todayCorrect: today.correct, todayWrong: today.wrong,
        perDayNew: perDay,
        behind: unlearned > perDay * remainingDays,
      };
    },

    daysLeft: function (targetDate) {
      var t = parseDate(targetDate);
      if (!t) return 0;
      var now = new Date();
      var a = new Date(now.getFullYear(), now.getMonth(), now.getDate());
      return Math.round((t - a) / DAY);
    },

    /** 生成今日任务序列：先到期复习 → 新题 → 少量混合 */
    buildTodayQueue: function (state, targetDate, opts) {
      opts = opts || {};
      var p = Practice.plan(state, targetDate);
      var due = Practice.poolDue(state);
      Bank.shuffle(due);
      var fresh = Practice.poolNew(state);
      Bank.shuffle(fresh);
      var mixed = [];
      var q = due.slice(0, opts.reviewLimit || 40)
        .concat(fresh.slice(0, opts.newLimit || p.perDayNew));
      var seenIds = {};
      q = q.filter(function (x) { if (seenIds[x.id]) return false; seenIds[x.id] = 1; return true; });
      if (opts.includeMixed && q.length < (opts.minTotal || 0)) {
        var extra = Bank.all.filter(function (x) { return !seenIds[x.id]; });
        Bank.shuffle(extra);
        q = q.concat(extra.slice(0, (opts.minTotal || 0) - q.length));
      }
      return q;
    },
  };

  function intervalOf(box) {
    var table = [0, 1, 2, 4, 7, 15, 30];   /* 天 */
    var d = table[Math.min(box, table.length - 1)] || 1;
    return d * DAY;
  }

  function pad(n) { return n < 10 ? '0' + n : '' + n; }

  function parseDate(s) {
    if (!s) return null;
    var m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(s));
    if (!m) return null;
    return new Date(+m[1], +m[2] - 1, +m[3]);
  }

  Practice.parseDate = parseDate;
  Practice.isoDate = function (d) {
    return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate());
  };
  window.Practice = Practice;
})();

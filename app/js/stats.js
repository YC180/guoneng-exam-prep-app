/* 统计层：覆盖率、正确率、掌握率、章节正确率、趋势、薄弱知识点。 */
(function () {
  'use strict';

  var Stats = {
    overview: function (state) {
      var total = Bank.all.length;
      var seen = 0, correctSum = 0, wrongSum = 0, mastered = 0, unverified = 0;
      var fav = 0, wrongQ = 0;
      Bank.all.forEach(function (q) {
        var r = state.progress[q.id];
        if (!r) return;
        if (r.seen) seen++;
        correctSum += r.correctCount || 0;
        wrongSum += r.wrongCount || 0;
        if (r.mastery === 'known') mastered++;
        if (r.fav) fav++;
        unverified += r.unverified || 0;
      });
      wrongQ = Object.keys(state.wrongBook || {}).length;
      var attempts = correctSum + wrongSum;
      return {
        total: total, seen: seen, unseen: total - seen,
        coverage: total ? seen / total : 0,
        attempts: attempts, correct: correctSum, wrong: wrongSum,
        accuracy: attempts ? correctSum / attempts : null,
        mastered: mastered, masteryRate: total ? mastered / total : 0,
        wrongQ: wrongQ, fav: fav, unverified: unverified,
        due: Practice.poolDue(state).length,
      };
    },

    /** 最近 N 天趋势（来自每日日志） */
    trend: function (state, days) {
      days = days || 7;
      var out = [];
      var base = new Date();
      for (var i = days - 1; i >= 0; i--) {
        var d = new Date(base.getFullYear(), base.getMonth(), base.getDate() - i);
        var key = Practice.isoDate(d);
        var log = (state.logs || {})[key] || { answered: 0, correct: 0, wrong: 0, minutes: 0 };
        out.push({
          date: key, label: (d.getMonth() + 1) + '/' + d.getDate(),
          answered: log.answered || 0, correct: log.correct || 0,
          wrong: log.wrong || 0, minutes: log.minutes || 0,
        });
      }
      return out;
    },

    /** 按类别/章节统计 */
    byChapter: function (state, category) {
      var rows = {};
      Bank.all.forEach(function (q) {
        if (category && q.category !== category) return;
        var ch = q.chapter || '未分类';
        rows[ch] = rows[ch] || { chapter: ch, category: q.category || '未分类', total: 0, seen: 0, correct: 0, wrong: 0, mastered: 0, due: 0 };
        var r = state.progress[q.id];
        rows[ch].total++;
        if (r) {
          if (r.seen) rows[ch].seen++;
          rows[ch].correct += r.correctCount || 0;
          rows[ch].wrong += r.wrongCount || 0;
          if (r.mastery === 'known') rows[ch].mastered++;
          if (r.seen && r.reviewDue && r.reviewDue <= Date.now()) rows[ch].due++;
        }
      });
      var list = Object.keys(rows).map(function (k) {
        var x = rows[k];
        var denom = x.correct + x.wrong;
        x.rate = denom ? x.correct / denom : null;
        x.coverage = x.total ? x.seen / x.total : 0;
        return x;
      });
      list.sort(function (a, b) {
        var ra = a.rate === null ? 2 : a.rate, rb = b.rate === null ? 2 : b.rate;
        if (ra !== rb) return ra - rb;
        return b.total - a.total;
      });
      return list;
    },

    /** 薄弱知识点：错得多、正确率低 */
    weakPoints: function (state, limit) {
      var rows = Stats.byChapter(state);
      var weak = rows.filter(function (x) { return x.wrong > 0 && (x.rate === null || x.rate < 0.75); });
      weak.sort(function (a, b) { return b.wrong - a.wrong; });
      return weak.slice(0, limit || 8);
    },

    /** 反复做错的题目 */
    stubborn: function (state, limit) {
      var wb = state.wrongBook || {};
      return Object.keys(wb).map(function (id) {
        return { q: Bank.byId[id], times: wb[id] };
      }).filter(function (x) { return x.q; })
        .sort(function (a, b) { return b.times - a.times; })
        .slice(0, limit || 10);
    },

    wrongReasonStats: function (state) {
      var out = {};
      Object.keys(state.wrongBook || {}).forEach(function (id) {
        var r = state.progress[id];
        var reason = (r && r.wrongReason) || '未记录';
        out[reason] = (out[reason] || 0) + 1;
      });
      return Object.keys(out).map(function (k) { return { reason: k, count: out[k] }; })
        .sort(function (a, b) { return b.count - a.count; });
    },
  };

  window.Stats = Stats;
})();

/* 题库层：加载内置题库 + 用户导入题库，建立索引，校验，筛选与排序。 */
(function () {
  'use strict';

  var TYPE_LABEL = {
    single_choice: '单选题', multiple_choice: '多选题', true_false: '判断题',
    fill_blank: '填空题', short_answer: '简答题',
  };

  var STATUS_LABEL = {
    verified: '已核对', needs_review: '待核对', missing: '无答案',
  };

  var Bank = {
    all: [],
    byId: {},
    custom: [],
    meta: {},
    loadInfo: {},
    facets: { categories: [], chapters: {}, types: [], tags: [] },
    TYPE_LABEL: TYPE_LABEL,
    STATUS_LABEL: STATUS_LABEL,

    /* ------------------------------------------------------------ 加载 */
    load: function () {
      var self = this;
      var staticBank = window.CE_BANK || { questions: [] };
      return Store.get('customBank', null).then(function (custom) {
        self.custom = (custom && custom.questions) ? custom.questions : [];
        self.meta = {
          schemaVersion: staticBank.schemaVersion || 1,
          generatedAt: staticBank.generatedAt || '',
          count: (staticBank.questions || []).length,
          customCount: self.custom.length,
        };
        var merged = [];
        var seen = {};
        function push(q, originTag) {
          if (!q || !q.stem) return;
          var key = self.normStem(q.stem) + '|' + (q.answer || []).join('');
          if (seen[key]) return;
          seen[key] = 1;
          q._origin = originTag;
          q.type = q.type || 'single_choice';
          if (!TYPE_LABEL[q.type]) q.type = 'single_choice';
          if (!q.answer) q.answer = [];
          if (!q.options) q.options = [];
          if (!q.tags) q.tags = [];
          if (!q.answerStatus) q.answerStatus = q.answer.length ? 'verified' : 'missing';
          merged.push(q);
        }
        (staticBank.questions || []).forEach(function (q) { push(q, 'builtin'); });
        self.custom.forEach(function (q) { push(q, 'imported'); });

        self.all = merged;
        self.byId = {};
        merged.forEach(function (q) { self.byId[q.id] = q; });
        self.buildFacets();
        self.loadInfo = {
          total: merged.length,
          builtin: merged.filter(function (q) { return q._origin === 'builtin'; }).length,
          imported: merged.filter(function (q) { return q._origin === 'imported'; }).length,
          generatedAt: self.meta.generatedAt,
        };
        return self.loadInfo;
      });
    },

    normStem: function (s) {
      return String(s || '').replace(/[\s\u3000]/g, '')
        .replace(/[，。、；：？！,.;:?!""''（）()【】\[\]…—\-_]+/g, '');
    },

    buildFacets: function () {
      var cats = {}, chapters = {}, types = {}, tags = {};
      this.all.forEach(function (q) {
        var c = q.category || '未分类';
        cats[c] = (cats[c] || 0) + 1;
        if (!chapters[c]) chapters[c] = {};
        var ch = q.chapter || '未分类';
        chapters[c][ch] = (chapters[c][ch] || 0) + 1;
        types[q.type] = (types[q.type] || 0) + 1;
        (q.tags || []).forEach(function (t) { tags[t] = (tags[t] || 0) + 1; });
      });
      this.facets = {
        categories: Object.keys(cats).sort(function (a, b) { return cats[b] - cats[a]; })
          .map(function (k) { return { name: k, count: cats[k] }; }),
        chapters: chapters,
        types: Object.keys(types).sort(function (a, b) { return types[b] - types[a]; })
          .map(function (k) { return { name: k, label: TYPE_LABEL[k] || k, count: types[k] }; }),
        tags: Object.keys(tags).sort(function (a, b) { return tags[b] - tags[a]; })
          .map(function (k) { return { name: k, count: tags[k] }; }),
      };
    },

    /* ---------------------------------------------------------- 校验器 */
    validate: function () {
      var issues = [];
      var ids = {};
      var dupIds = [];
      var byIssue = {};
      function add(q, kind) {
        issues.push({ id: q.id, kind: kind, stem: (q.stem || '').slice(0, 60), source: q.sourceFile || '' });
        byIssue[kind] = (byIssue[kind] || 0) + 1;
      }
      this.all.forEach(function (q) {
        if (ids[q.id]) dupIds.push(q.id); else ids[q.id] = 1;
        if (!(q.stem || '').trim()) add(q, '题干为空');
        if (q.type === 'single_choice' || q.type === 'multiple_choice') {
          if ((q.options || []).length < 2) add(q, '选项缺失或不足');
          var keys = {};
          (q.options || []).forEach(function (o) { keys[o.key] = 1; if (!(o.text || '').trim()) add(q, '选项文本为空'); });
          if (!(q.answer || []).length) add(q, '答案缺失');
          (q.answer || []).forEach(function (a) { if (!keys[a]) add(q, '答案选项不存在'); });
          if (q.type === 'single_choice' && (q.answer || []).length > 1) add(q, '单选却有多答案');
          if (q.type === 'multiple_choice' && (q.answer || []).length < 2) add(q, '多选却只有一个答案');
        } else if (!(q.answer || []).length) {
          add(q, '答案缺失');
        }
        if (!(q.explanation || '').trim()) add(q, '解析缺失（非错误）');
        if (!q.sourceFile) add(q, '来源缺失');
        if (q.answerStatus === 'needs_review') add(q, '答案待核对');
      });
      return {
        total: this.all.length,
        duplicateIds: dupIds,
        issueCount: issues.length,
        byIssue: byIssue,
        issues: issues,
      };
    },

    /* ---------------------------------------------------------- 筛选 */
    filter: function (o) {
      o = o || {};
      var kw = (o.keyword || '').trim().toLowerCase();
      var kwTokens = kw ? kw.split(/\s+/) : [];
      var out = this.all.filter(function (q) {
        if (o.category && q.category !== o.category) return false;
        if (o.chapter && q.chapter !== o.chapter) return false;
        if (o.type && q.type !== o.type) return false;
        if (o.tag && (q.tags || []).indexOf(o.tag) < 0) return false;
        if (o.status && (q.answerStatus || 'missing') !== o.status) return false;
        if (o.onlyEnabled && q.enabled === false) return false;
        if (kwTokens.length) {
          var hay = ((q.stem || '') + ' ' + (q.options || []).map(function (x) { return x.text; }).join(' ')
            + ' ' + (q.explanation || '') + ' ' + (q.chapter || '')).toLowerCase();
          for (var i = 0; i < kwTokens.length; i++) {
            if (hay.indexOf(kwTokens[i]) < 0) return false;
          }
        }
        return true;
      });
      return out;
    },

    sort: function (list, mode, prog) {
      var arr = list.slice();
      prog = prog || {};
      function p(q) { return prog[q.id] || {}; }
      switch (mode) {
        case 'wrong':
          arr.sort(function (a, b) { return (p(b).wrongCount || 0) - (p(a).wrongCount || 0); }); break;
        case 'new':
          arr.sort(function (a, b) { return (p(a).seen ? 1 : 0) - (p(b).seen ? 1 : 0); }); break;
        case 'recent':
          arr.sort(function (a, b) { return (p(b).lastAt || 0) - (p(a).lastAt || 0); }); break;
        case 'rate':
          arr.sort(function (a, b) {
            var ra = rate(p(a)), rb = rate(p(b));
            return ra - rb;
          }); break;
        default: break; /* 原始顺序 */
      }
      return arr;
    },

    /** 生成一份试卷/练习序列 */
    pick: function (opts) {
      opts = opts || {};
      var list = opts.pool || this.all;
      list = list.slice();
      if (opts.shuffle) shuffle(list);
      else if (opts.seedShuffle) { /* 保持稳定顺序 */ }
      if (opts.limit && list.length > opts.limit) list = list.slice(0, opts.limit);
      return list;
    },

    typeLabel: function (t) { return TYPE_LABEL[t] || t; },
    statusLabel: function (s) { return STATUS_LABEL[s || 'missing'] || s; },
  };

  function rate(p) {
    var t = (p.correctCount || 0) + (p.wrongCount || 0);
    if (!t) return -1;
    return (p.correctCount || 0) / t;
  }

  function shuffle(a) {
    for (var i = a.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var t = a[i]; a[i] = a[j]; a[j] = t;
    }
    return a;
  }

  Bank.shuffle = shuffle;
  window.Bank = Bank;
})();

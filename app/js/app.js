/* 应用控制器：状态、路由、事件、快捷键、考试计时、会话续做。 */
(function () {
  'use strict';

  var App = {
    state: {
      meta: { targetDate: '2026-10-24', settings: { fontScale: 1, dark: false, dailyNew: 0, onePerScreen: true } },
      progress: {}, wrongBook: {}, logs: {}, exams: [], session: null,
      currentExam: null, examResult: null,
    },
    view: 'home',
    params: {},
    ready: false,
  };

  var SAVE_KEYS = ['meta', 'progress', 'wrongBook', 'logs', 'exams', 'session', 'currentExam'];

  /* ------------------------------------------------------------ 持久化 */
  App.save = function (immediate) {
    var jobs = SAVE_KEYS.map(function (k) {
      return Store.set(k, App.state[k]);
    });
    return Promise.all(jobs);
  };

  App.saveDebounced = (function () {
    var t = null;
    return function () {
      if (t) clearTimeout(t);
      t = setTimeout(function () { App.save(); }, 400);
    };
  })();

  App.persistSession = function () { Store.set('session', App.state.session); };

  App.toast = function (msg, ms) {
    var host = document.getElementById('toastHost');
    host.innerHTML = '<div class="toast">' + UI.esc(msg) + '</div>';
    setTimeout(function () { host.innerHTML = ''; }, ms || 2200);
  };

  /* ------------------------------------------------------------ 主题 */
  App.applyTheme = function () {
    var st = App.state.meta.settings || {};
    document.documentElement.setAttribute('data-theme', st.dark ? 'dark' : 'light');
    document.documentElement.style.setProperty('--fs-scale', String(st.fontScale || 1));
    document.getElementById('btnTheme').textContent = st.dark ? '浅色' : '深色';
  };

  /* ------------------------------------------------------------ 路由 */
  App.go = function (view, params) {
    App.view = view;
    App.params = params || {};
    if (view !== 'exam') { /* 保留考试状态 */ }
    App.render();
    window.scrollTo({ top: 0, behavior: 'auto' });
  };

  App.render = function () {
    var v = document.getElementById('view');
    var navBtns = document.querySelectorAll('#nav button');
    navBtns.forEach(function (b) {
      b.setAttribute('aria-current', b.getAttribute('data-go') === App.view ? 'true' : 'false');
    });
    var titles = {
      home: ['首页', ''], bank: ['题库', ''], practice: ['练习', ''],
      wrong: ['错题本', ''], exam: ['模拟考', ''], stats: ['统计', ''], more: ['资料与设置', ''],
    };
    var t = titles[App.view] || ['', ''];
    document.getElementById('ttl').innerHTML = UI.esc(t[0]) +
      '<span class="sub" id="ttlSub"> ' + (App.view === 'bank' ? (Bank.all.length + ' 题') : '') + '</span>';

    var html;
    try {
      switch (App.view) {
        case 'bank': html = UI.viewBank(App.state, App.params); break;
        case 'question': html = UI.viewQuestion(App.state, App.params); break;
        case 'practice': html = UI.viewPractice(App.state); break;
        case 'wrong': html = UI.viewWrong(App.state); break;
        case 'exam': html = UI.viewExam(App.state); break;
        case 'stats': html = UI.viewStats(App.state); break;
        case 'more': html = UI.viewMore(App.state); break;
        default: html = UI.viewHome(App.state);
      }
    } catch (e) {
      html = '<div class="card"><h2>页面渲染出错</h2><div class="feedback bad">' +
        UI.esc(e && e.message ? e.message : String(e)) + '</div>' +
        '<div class="hint">请刷新页面重试。若问题持续，可在“资料与设置”中导出备份后清空学习数据。</div></div>';
      if (window.console) console.error(e);
    }
    v.innerHTML = html;
    App.afterRender();
  };

  App.afterRender = function () {
    /* 题目中的选项点击在全局委托中处理；此处恢复输入框内容 */
    var s = App.state.session;
    if (App.view === 'practice' && s && s.queue && s.queue.length) {
      var qid = s.queue[s.idx];
      var inp = document.getElementById('qInput');
      if (inp) inp.value = (s.ua[qid] || [])[0] || '';
    }
    /* 深色模式下选项按钮的 aria-pressed 由状态决定，已在模板中渲染 */
  };

  /* ------------------------------------------------------- 当前题目 */
  function currentQid() {
    if (App.state.currentExam && App.view === 'exam') {
      var e = App.state.currentExam;
      return e.qids[e.cursor || 0];
    }
    var s = App.state.session;
    if (s && s.queue && s.queue.length) return s.queue[s.idx];
    return null;
  }

  function currentAnswerArray() {
    var qid = currentQid();
    if (!qid) return null;
    if (App.state.currentExam && App.view === 'exam') {
      var e = App.state.currentExam;
      e.answers[qid] = e.answers[qid] || [];
      return e.answers[qid];
    }
    var s = App.state.session;
    if (s) {
      s.ua[qid] = s.ua[qid] || [];
      return s.ua[qid];
    }
    return null;
  }

  /* ------------------------------------------------------- 练习启动 */
  function startToday(state) {
    var target = (state.meta && state.meta.targetDate) || '2026-10-24';
    var queue = Practice.buildTodayQueue(state, target, { reviewLimit: 40, newLimit: 0 });
    if (!queue.length) {
      var p = Practice.plan(state, target);
      queue = Practice.buildTodayQueue(state, target, { newLimit: p.perDayNew, reviewLimit: 20 });
    }
    state.session = {
      mode: 'today', title: '今日学习', queue: queue.map(function (q) { return q.id; }),
      idx: 0, submitted: {}, ua: {}, result: {}, startedAt: Date.now(),
    };
    App.persistSession();
    App.go('practice');
  }

  function startOne(state, qid) {
    state.session = {
      mode: 'one', title: '单题练习', queue: [qid], idx: 0,
      submitted: {}, ua: {}, result: {}, startedAt: Date.now(),
    };
    App.persistSession();
    App.go('practice');
  }

  /* ------------------------------------------------------------ 事件 */
  function onClick(ev) {
    var t = ev.target.closest('[data-act],[data-go],[data-open-q],[data-page],[data-tag],[data-pmode],[data-opt],[data-level],[data-idx],[data-eid]');
    if (!t) return;
    var act = t.getAttribute('data-act');
    var go = t.getAttribute('data-go');

    if (go) { ev.preventDefault(); App.go(go); return; }

    /* 选项点击 */
    if (t.hasAttribute('data-opt')) { ev.preventDefault(); onOption(t); return; }

    var openQ = t.getAttribute('data-open-q');
    if (openQ) { ev.preventDefault(); App.go('question', { qid: openQ }); return; }

    var page = t.getAttribute('data-page');
    if (page !== null) { ev.preventDefault(); App.go('bank', { page: parseInt(page, 10) || 0 }); return; }

    var tag = t.getAttribute('data-tag');
    if (tag !== null) {
      ev.preventDefault();
      UI.bankFilter.tag = (UI.bankFilter.tag === tag) ? '' : tag;
      App.go('bank', { page: 0 });
      return;
    }

    var pmode = t.getAttribute('data-pmode');
    if (pmode) {
      ev.preventDefault();
      UI.practiceStart.mode = pmode;
      App.render();
      return;
    }

    var idx = t.getAttribute('data-idx');
    if (idx !== null && act === 'e-goto') {
      App.state.currentExam.cursor = parseInt(idx, 10) || 0;
      App.render();
      return;
    }

    var eid = t.getAttribute('data-eid');
    if (act === 'e-review' && eid) {
      var rec = (App.state.exams || []).filter(function (x) { return x.id === eid; })[0];
      if (rec) {
        App.state.examResult = { exam: rec, result: rec.result };
        App.go('exam');
      }
      return;
    }

    if (!act) return;
    ev.preventDefault();
    handleAction(act, t);
  }

  function onOption(btn) {
    var qid = currentQid();
    if (!qid) return;
    var q = Bank.byId[qid];
    if (!q) return;
    var key = btn.getAttribute('data-opt');
    var submitted = false;
    if (App.state.currentExam && App.view === 'exam') {
      submitted = !!App.state.currentExam.showAnswerPerQuestion;
    } else if (App.state.session) {
      submitted = !!App.state.session.submitted[qid];
    }
    if (submitted) return;   /* 已判分后不允许改答案 */

    var arr = currentAnswerArray();
    if (!arr) return;
    var multi = q.type === 'multiple_choice';
    if (multi) {
      var i = arr.indexOf(key);
      if (i >= 0) arr.splice(i, 1); else arr.push(key);
      btn.setAttribute('aria-pressed', i >= 0 ? 'false' : 'true');
    } else {
      /* 单选 / 判断：替换 */
      arr.length = 0;
      arr.push(key);
      var container = btn.parentNode;
      Array.prototype.forEach.call(container.querySelectorAll('[data-opt]'), function (b) {
        b.setAttribute('aria-pressed', b === btn ? 'true' : 'false');
      });
    }
    if (q.type === 'true_false') {
      /* 判断题选项为 正确/错误，内部统一保存为中文枚举 */
    }
    updateAnsweredCount();
    App.persistSession();
    App.saveDebounced();
    if (App.state.currentExam) Store.set('currentExam', App.state.currentExam);
  }

  function updateAnsweredCount() {
    var e = App.state.currentExam;
    if (!e || App.view !== 'exam') return;
    var n = Object.keys(e.answers).filter(function (k) { return e.answers[k] && e.answers[k].length; }).length;
    var nodes = document.querySelectorAll('#view .muted');
    /* 简单策略：仅更新顶部计数条 */
    var top = document.querySelector('#view .card.tight .row.between .muted');
    if (top && /已答/.test(top.textContent)) top.textContent = '已答 ' + n + ' / ' + e.qids.length;
  }

  function handleAction(act, el) {
    var state = App.state;
    switch (act) {
      /* ---------------- 首页 ---------------- */
      case 'today': startToday(state); break;
      case 'resume':
        if (state.session && state.session.queue && state.session.queue.length) App.go('practice');
        else App.toast('没有可继续的练习，先从“开始今日学习”开始。');
        break;
      case 'wrong-practice': App.go('wrong'); break;
      case 'go-exam': App.go('exam'); break;
      case 'due-practice':
        UI.startPractice(state, 'due', { limit: 50 });
        App.go('practice');
        break;

      /* ---------------- 题库 ---------------- */
      case 'bank-reset':
        UI.bankFilter.keyword = ''; UI.bankFilter.category = ''; UI.bankFilter.chapter = '';
        UI.bankFilter.type = ''; UI.bankFilter.tag = ''; UI.bankFilter.status = ''; UI.bankFilter.sort = 'default';
        App.go('bank', { page: 0 });
        break;
      case 'bank-practice': {
        var list = Bank.filter(UI.bankFilter);
        if (!list.length) { App.toast('当前筛选结果为空。'); break; }
        var pick = Bank.pick({ pool: list, shuffle: true, limit: Math.min(50, list.length) });
        state.session = {
          mode: 'filtered', title: '筛选结果练习', queue: pick.map(function (q) { return q.id; }),
          idx: 0, submitted: {}, ua: {}, result: {}, startedAt: Date.now(),
        };
        App.persistSession();
        App.go('practice');
        break;
      }
      case 'bank-back': App.go('bank'); break;

      /* ---------------- 题目详情 ---------------- */
      case 'fav': {
        var on = Practice.toggleFav(state, el.getAttribute('data-qid'));
        App.toast(on ? '已收藏' : '已取消收藏');
        App.save(); App.render();
        break;
      }
      case 'mastery': {
        Practice.setMastery(state, el.getAttribute('data-qid'), el.getAttribute('data-level'));
        App.toast('已标记');
        App.save(); App.render();
        break;
      }
      case 'save-reason': {
        var inp = document.getElementById('wrongReason');
        Practice.setWrongReason(state, el.getAttribute('data-qid'), inp ? inp.value : '');
        App.toast('错因已保存');
        App.save();
        break;
      }
      case 'remove-wrong':
        Practice.removeWrong(state, el.getAttribute('data-qid'));
        App.toast('已从错题本移除');
        App.save(); App.render();
        break;
      case 'practice-one': startOne(state, el.getAttribute('data-qid')); break;

      /* ---------------- 练习 ---------------- */
      case 'p-start': {
        var limit = parseInt((document.getElementById('pLimit') || {}).value, 10) || 30;
        var cat = (document.getElementById('pCat') || {}).value || '';
        var ch = (document.getElementById('pCh') || {}).value || '';
        UI.startPractice(state, UI.practiceStart.mode, { limit: limit, category: cat, chapter: ch });
        if (!state.session.queue.length) { App.toast('该范围内没有题目。'); break; }
        App.go('practice');
        break;
      }
      case 'p-submit': {
        var s = state.session;
        if (!s) break;
        var qid = s.queue[s.idx];
        var q = Bank.byId[qid];
        if (!q) break;
        var ua = s.ua[qid] || [];
        var inp2 = document.getElementById('qInput');
        if (inp2) { ua = [inp2.value]; s.ua[qid] = ua; }
        if (!ua.length || !String(ua[0] || '').trim()) {
          if (!confirm('本题尚未作答，仍要提交吗？')) break;
        }
        var res = Practice.answer(state, q, ua);
        s.result[qid] = res;
        s.submitted[qid] = true;
        App.save();
        App.render();
        break;
      }
      case 'p-next': {
        var s2 = state.session;
        if (!s2) break;
        if (s2.idx + 1 >= s2.queue.length) { finishSession(); break; }
        s2.idx += 1;
        s2.cursor = s2.idx;
        App.persistSession();
        App.render();
        break;
      }
      case 'p-prev': {
        var s3 = state.session;
        if (!s3 || s3.idx <= 0) break;
        s3.idx -= 1;
        App.persistSession();
        App.render();
        break;
      }
      case 'p-quit':
        if (confirm('退出本次练习？进度已保存，可从“继续上次学习”恢复。')) {
          App.persistSession();
          App.go('home');
        }
        break;
      case 'p-finish':
        finishSession();
        break;
      case 'p-fav': {
        Practice.toggleFav(state, el.getAttribute('data-qid'));
        App.save(); App.render();
        break;
      }
      case 'p-mastery':
        Practice.setMastery(state, el.getAttribute('data-qid'), el.getAttribute('data-level'));
        App.save(); App.render();
        break;

      /* ---------------- 错题本 ---------------- */
      case 'w-practice':
        if (!Object.keys(state.wrongBook || {}).length) { App.toast('错题本是空的。'); break; }
        UI.startPractice(state, 'wrong', { limit: 50 });
        App.go('practice');
        break;
      case 'w-due': {
        var dueList = Practice.poolDue(state).filter(function (q) { return state.wrongBook[q.id]; });
        if (!dueList.length) { App.toast('今天没有到期的错题。'); break; }
        state.session = {
          mode: 'wrong', title: '到期错题复习', queue: dueList.map(function (q) { return q.id; }),
          idx: 0, submitted: {}, ua: {}, result: {}, startedAt: Date.now(),
        };
        App.persistSession();
        App.go('practice');
        break;
      }
      case 'w-clear':
        if (confirm('确定清空错题本吗？题目本身与答题记录不会被删除，但错题计数会归零。')) {
          state.wrongBook = {};
          App.save(); App.render();
        }
        break;

      /* ---------------- 模拟考 ---------------- */
      case 'e-start': {
        var count = parseInt((document.getElementById('eCount') || {}).value, 10) || 100;
        var dur = parseInt((document.getElementById('eDur') || {}).value, 10) || 60;
        var ecat = (document.getElementById('eCat') || {}).value || '';
        var ech = (document.getElementById('eCh') || {}).value || '';
        var live = !!(document.getElementById('eLive') || {}).checked;
        var pool = Bank.filter({ category: ecat, chapter: ech }).filter(function (q) {
          return q.type === 'single_choice' || q.type === 'multiple_choice' || q.type === 'true_false';
        });
        if (!pool.length) { App.toast('该范围内没有可用于考试的题目。'); break; }
        var exam = Exam.create(state, {
          count: count, durationMin: dur, pool: pool, showAnswerPerQuestion: live,
          scope: (ecat || '全部题库') + (ech ? ' / ' + ech : ''),
        });
        exam.cursor = 0; exam.showCard = false;
        state.examResult = null;
        Store.set('currentExam', exam);
        App.go('exam');
        break;
      }
      case 'e-card':
        state.currentExam.showCard = !state.currentExam.showCard;
        App.render();
        break;
      case 'e-flag': {
        var e = state.currentExam;
        var fq = el.getAttribute('data-qid');
        e.flagged[fq] = !e.flagged[fq];
        App.render();
        break;
      }
      case 'e-prev':
        state.currentExam.cursor = Math.max(0, (state.currentExam.cursor || 0) - 1);
        App.render();
        break;
      case 'e-next':
        state.currentExam.cursor = Math.min(state.currentExam.qids.length - 1, (state.currentExam.cursor || 0) + 1);
        App.render();
        break;
      case 'e-submit': {
        var ex = state.currentExam;
        var unanswered = ex.qids.filter(function (qid) { return !(ex.answers[qid] || []).length; }).length;
        var msg = unanswered ? ('还有 ' + unanswered + ' 题未作答，确定交卷？') : '确定交卷？';
        if (!confirm(msg)) break;
        var result = Exam.submit(state, ex);
        state.examResult = { exam: state.exams[0], result: result };
        Store.set('currentExam', null);
        App.save();
        App.go('exam');
        break;
      }
      case 'e-again':
        state.examResult = null;
        App.go('exam');
        break;
      case 'e-back':
        state.examResult = null;
        App.go('exam');
        break;

      /* ---------------- 设置与数据 ---------------- */
      case 'save-settings': {
        var td = (document.getElementById('setTarget') || {}).value;
        var dn = parseInt((document.getElementById('setDailyNew') || {}).value, 10) || 0;
        var fs = parseFloat((document.getElementById('setFont') || {}).value) || 1;
        var dk = !!(document.getElementById('setDark') || {}).checked;
        var op = !!(document.getElementById('setOnePer') || {}).checked;
        state.meta.targetDate = td || '2026-10-24';
        state.meta.settings = { fontScale: fs, dark: dk, dailyNew: dn, onePerScreen: op };
        App.applyTheme();
        App.save().then(function () { App.toast('设置已保存'); App.render(); });
        break;
      }
      case 'exp-progress': IO.exportProgress(state); App.toast('已导出学习记录'); break;
      case 'exp-bank': IO.exportBank(state); App.toast('已导出题库'); break;
      case 'exp-backup': IO.exportBackup(state); App.toast('已导出完整备份'); break;
      case 'exp-valid':
        IO.exportValidation(Bank.validate(), Bank.loadInfo);
        App.toast('已导出校验报告');
        break;
      case 'tpl': IO.csvTemplate(); App.toast('模板已下载'); break;
      case 'imp': document.getElementById('fileInput').click(); break;
      case 'validate': {
        var rep = Bank.validate();
        var box = document.getElementById('impPreview');
        var s = '<div class="card"><h2>校验结果</h2><div class="grid3">' +
          '<div class="stat"><div class="v">' + rep.total + '</div><div class="k">题目总数</div></div>' +
          '<div class="stat"><div class="v">' + rep.duplicateIds.length + '</div><div class="k">重复 ID</div></div>' +
          '<div class="stat"><div class="v">' + rep.issueCount + '</div><div class="k">异常条目</div></div>' +
          '</div><div class="scrollx" style="margin-top:10px"><table class="tbl"><tr><th>异常类型</th><th class="num">数量</th></tr>';
        Object.keys(rep.byIssue).sort(function (a, b) { return rep.byIssue[b] - rep.byIssue[a]; })
          .forEach(function (k) { s += '<tr><td>' + UI.esc(k) + '</td><td class="num">' + rep.byIssue[k] + '</td></tr>'; });
        s += '</table></div><div class="hint">“解析缺失”不是错误。可用“导出题库校验报告”保存完整明细。</div></div>';
        box.innerHTML = s;
        break;
      }
      case 'wipe':
        if (confirm('确定清空全部学习数据吗？此操作不可撤销。建议先导出完整备份。')) {
          if (confirm('再次确认：清空答题记录、错题本、收藏与考试记录？')) {
            Store.clearAll().then(function () {
              App.state.progress = {}; App.state.wrongBook = {}; App.state.logs = {};
              App.state.exams = []; App.state.session = null;
              App.state.currentExam = null; App.state.examResult = null;
              App.render();
              App.toast('学习数据已清空');
            });
          }
        }
        break;
      default: break;
    }
  }

  function finishSession() {
    var s = App.state.session;
    if (!s) return;
    var done = Object.keys(s.submitted || {}).length;
    var right = Object.keys(s.result || {}).filter(function (k) { return s.result[k] && s.result[k].correct === true; }).length;
    App.toast('本次练习完成：作答 ' + done + ' 题，答对 ' + right + ' 题', 3000);
    App.state.session = null;
    Store.set('session', null);
    App.save();
    App.go('home');
  }

  /* --------------------------------------------------- 筛选控件事件 */
  function onChange(ev) {
    var id = ev.target.id;
    var f = UI.bankFilter;
    switch (id) {
      case 'bankCat':
        f.category = ev.target.value; f.chapter = '';
        App.go('bank', { page: 0 }); return;
      case 'bankCh': f.chapter = ev.target.value; App.go('bank', { page: 0 }); return;
      case 'bankType': f.type = ev.target.value; App.go('bank', { page: 0 }); return;
      case 'bankStatus': f.status = ev.target.value; App.go('bank', { page: 0 }); return;
      case 'bankSort': f.sort = ev.target.value; App.go('bank', { page: 0 }); return;
      case 'wSort': UI.wrongFilter.sort = ev.target.value; App.render(); return;
      case 'wChapter': UI.wrongFilter.chapter = ev.target.value; App.render(); return;
      case 'wReason': UI.wrongFilter.reason = ev.target.value; App.render(); return;
      case 'eCat': UI.examSetup.category = ev.target.value; UI.examSetup.chapter = ''; App.render(); return;
      case 'eCh': UI.examSetup.chapter = ev.target.value; App.render(); return;
      case 'pCat': UI.practiceStart.category = ev.target.value; UI.practiceStart.chapter = ''; App.render(); return;
      case 'pCh': UI.practiceStart.chapter = ev.target.value; App.render(); return;
      case 'setDark':
        App.state.meta.settings.dark = ev.target.checked; App.applyTheme(); return;
      default: return;
    }
  }

  var kwTimer = null;
  function onInput(ev) {
    if (ev.target.id === 'bankKw') {
      var val = ev.target.value;
      if (kwTimer) clearTimeout(kwTimer);
      kwTimer = setTimeout(function () {
        UI.bankFilter.keyword = val;
        App.go('bank', { page: 0 });
      }, 320);
      return;
    }
    if (ev.target.id === 'qInput') {
      var s = App.state.session;
      var qid = currentQid();
      if (s && qid) { s.ua[qid] = [ev.target.value]; App.saveDebounced(); }
    }
  }

  /* ------------------------------------------------------- 文件导入 */
  function onFile(ev) {
    var file = ev.target.files && ev.target.files[0];
    if (!file) return;
    var reader = new FileReader();
    reader.onload = function () {
      var text = String(reader.result || '');
      var parsed;
      try {
        parsed = /\.csv$/i.test(file.name) || text.trim().charAt(0) !== '{' && text.indexOf('{') !== 0
          ? IO.parseCSV(text) : IO.parseJSON(text);
        if (parsed.kind === 'ce-study-progress' || parsed.kind === 'ce-full-backup') {
          showProgressImport(parsed.raw, file.name);
          return;
        }
      } catch (e) {
        try { parsed = IO.parseJSON(text); }
        catch (e2) {
          App.toast('文件解析失败：' + e2.message, 4000);
          return;
        }
      }
      if (parsed.kind === 'ce-study-progress' || parsed.kind === 'ce-full-backup') {
        showProgressImport(parsed.raw, file.name);
        return;
      }
      var v = IO.validateImport(parsed.questions);
      var box = document.getElementById('impPreview');
      var s = '<div class="card"><h2>导入预览：' + UI.esc(file.name) + '</h2>' +
        '<div class="grid3"><div class="stat"><div class="v">' + v.count + '</div><div class="k">题目条数</div></div>' +
        '<div class="stat"><div class="v">' + v.issues.length + '</div><div class="k">校验提示</div></div>' +
        '<div class="stat"><div class="v">' + parsed.kind + '</div><div class="k">文件类型</div></div></div>';
      if (v.issues.length) {
        s += '<div class="feedback warn" style="margin-top:10px">校验发现问题（仍可导入，问题条目会标为待核对）：' +
          '<ul class="tight">' + v.issues.slice(0, 12).map(function (x) { return '<li>' + UI.esc(x) + '</li>'; }).join('') +
          (v.issues.length > 12 ? '<li>…… 其余 ' + (v.issues.length - 12) + ' 条见导出报告</li>' : '') + '</ul></div>';
      }
      s += '<div class="row" style="margin-top:10px">' +
        '<button class="btn-primary" data-act="imp-do" data-mode="append">追加导入（保留原有导入题库）</button>' +
        '<button data-act="imp-do" data-mode="replace">替换导入题库</button>' +
        '<button data-act="imp-cancel">取消</button></div>' +
        '<div class="hint">导入的题目单独存储，不会修改内置题库。</div></div>';
      box.innerHTML = s;
      box._pending = { questions: parsed.questions, kind: parsed.kind };
      /* 追加导入的按钮事件 */
      box.querySelectorAll('[data-act="imp-do"]').forEach(function (b) {
        b.addEventListener('click', function () {
          var mode = b.getAttribute('data-mode');
          IO.applyBank(box._pending.questions, mode).then(function (r) {
            App.toast('导入完成：新增 ' + r.added + ' 题，跳过重复 ' + r.skipped + ' 题', 3500);
            return Bank.load();
          }).then(function () {
            box.innerHTML = '';
            App.render();
          });
        });
      });
      var cancel = box.querySelector('[data-act="imp-cancel"]');
      if (cancel) cancel.addEventListener('click', function () { box.innerHTML = ''; });
    };
    reader.readAsText(file, 'utf-8');
    ev.target.value = '';
  }

  function showProgressImport(payload, name) {
    var box = document.getElementById('impPreview');
    var p = payload.progress || {};
    var s = '<div class="card"><h2>恢复备份：' + UI.esc(name) + '</h2>' +
      '<div class="grid3"><div class="stat"><div class="v">' + Object.keys(p).length + '</div><div class="k">题目记录</div></div>' +
      '<div class="stat"><div class="v">' + Object.keys(payload.wrongBook || {}).length + '</div><div class="k">错题</div></div>' +
      '<div class="stat"><div class="v">' + ((payload.exams || []).length) + '</div><div class="k">考试记录</div></div></div>' +
      (payload.customBank && payload.customBank.questions
        ? '<div class="hint">该备份包含导入题库 ' + payload.customBank.questions.length + ' 题，将一并恢复。</div>' : '') +
      '<div class="row" style="margin-top:10px">' +
      '<button class="btn-primary" data-act="res-merge">合并恢复（保留现有记录）</button>' +
      '<button data-act="res-replace">替换恢复（覆盖现有记录）</button>' +
      '<button data-act="imp-cancel">取消</button></div></div>';
    box.innerHTML = s;
    function doRestore(mode) {
      var chain = Promise.resolve();
      if (payload.customBank && payload.customBank.questions) {
        chain = IO.applyBank(payload.customBank.questions, mode === 'replace' ? 'replace' : 'append');
      }
      chain.then(function () { return IO.applyProgress(payload, mode); })
        .then(function (r) {
          App.toast('恢复完成：' + r.progress + ' 条题目记录，' + r.wrong + ' 道错题', 3500);
          return Bank.load();
        })
        .then(function () { return App.loadState(); })
        .then(function () {
          App.applyTheme();
          box.innerHTML = '';
          App.render();
        })
        .catch(function (e) { App.toast('恢复失败：' + e.message, 4000); });
    }
    box.querySelector('[data-act="res-merge"]').addEventListener('click', function () { doRestore('merge'); });
    box.querySelector('[data-act="res-replace"]').addEventListener('click', function () { doRestore('replace'); });
    var cancel = box.querySelector('[data-act="imp-cancel"]');
    if (cancel) cancel.addEventListener('click', function () { box.innerHTML = ''; });
  }

  /* ------------------------------------------------------- 快捷键 */
  function onKey(ev) {
    if (ev.target && /INPUT|TEXTAREA|SELECT/.test(ev.target.tagName)) {
      if (ev.key === 'Enter' && ev.target.id === 'qInput') { onEnter(); }
      return;
    }
    if (App.view !== 'practice' && App.view !== 'exam') return;
    var k = ev.key.toUpperCase();
    if (ev.key === 'Escape') {
      if (App.view === 'practice' && App.state.session) {
        App.persistSession();
        App.go('home');
      }
      return;
    }
    if (ev.key === 'Enter') { onEnter(); return; }
    if (/^[A-H]$/.test(k)) {
      var btn = document.querySelector('#view [data-opt="' + k + '"]');
      if (btn) { btn.click(); }
      else {
        /* 判断题：A→正确，B→错误 */
        var qid = currentQid();
        var q = qid ? Bank.byId[qid] : null;
        if (q && q.type === 'true_false') {
          var target = document.querySelector('#view [data-opt="' + (k === 'A' ? '正确' : k === 'B' ? '错误' : '') + '"]');
          if (target) target.click();
        }
      }
    }
  }

  function onEnter() {
    if (App.view === 'practice') {
      var s = App.state.session;
      if (!s) return;
      var qid = s.queue[s.idx];
      if (!s.submitted[qid]) {
        var btn = document.querySelector('#view [data-act="p-submit"]');
        if (btn) btn.click();
      } else {
        var nb = document.querySelector('#view [data-act="p-next"]');
        if (nb) nb.click();
      }
    } else if (App.view === 'exam') {
      var nb2 = document.querySelector('#view [data-act="e-next"]');
      if (nb2) nb2.click();
    }
  }

  /* --------------------------------------------------- 考试倒计时 */
  var examTimer = null;
  function tickExam() {
    var e = App.state.currentExam;
    if (!e || App.view !== 'exam') return;
    var rem = Exam.remaining(e);
    var node = document.getElementById('examTimer');
    if (node) {
      node.textContent = Exam.fmt(rem);
      node.className = 'timer' + (rem < 300 ? ' low' : '');
    }
    if (rem <= 0 && !e.autoSubmitted) {
      e.autoSubmitted = true;
      App.toast('考试时间到，已自动交卷', 3500);
      var result = Exam.submit(App.state, e);
      App.state.examResult = { exam: App.state.exams[0], result: result };
      Store.set('currentExam', null);
      App.save();
      App.go('exam');
    }
  }

  /* ------------------------------------------------------- 会话计时 */
  var sessionTimer = null;
  function tickSession() {
    var s = App.state.session;
    if (!s || !s.startedAt) return;
    var mins = Math.floor((Date.now() - s.startedAt) / 60000);
    if (mins > 0 && mins !== s._loggedMins) {
      var delta = mins - (s._loggedMins || 0);
      s._loggedMins = mins;
      Practice.addMinutes(App.state, delta);
      App.saveDebounced();
    }
  }

  /* ------------------------------------------------------------ 启动 */
  App.loadState = function () {
    var keys = ['meta', 'progress', 'wrongBook', 'logs', 'exams', 'session', 'currentExam'];
    return Promise.all(keys.map(function (k) { return Store.get(k, null); }))
      .then(function (vals) {
        keys.forEach(function (k, i) {
          var v = vals[i];
          if (v === null || v === undefined) return;
          if (k === 'meta') {
            App.state.meta = v;
            App.state.meta.settings = App.state.meta.settings || { fontScale: 1, dark: false, dailyNew: 0, onePerScreen: true };
            if (!App.state.meta.targetDate) App.state.meta.targetDate = '2026-10-24';
          } else {
            App.state[k] = v;
          }
        });
        return true;
      });
  };

  function boot() {
    Store.init().then(function (backend) {
      return App.loadState().then(function () {
        return Bank.load();
      });
    }).then(function () {
      App.applyTheme();
      App.ready = true;
      /* 若存在未交卷的考试，直接回到考试页 */
      if (App.state.currentExam && !App.state.currentExam.submitted) {
        App.state.currentExam.cursor = App.state.currentExam.cursor || 0;
        App.go('exam');
      } else {
        App.go('home');
      }
      if (Store.backendName() === 'mem') {
        App.toast('警告：当前环境无法持久化数据，关闭页面后记录会丢失。请使用 start.cmd 以 http 方式打开。', 6000);
      }
      /* 计时器 */
      examTimer = setInterval(tickExam, 1000);
      sessionTimer = setInterval(tickSession, 20000);
      /* 首次使用提示 */
      if (!localStorage.getItem('ce_study::seenIntro')) {
        setTimeout(function () {
          App.toast('已载入题库 ' + Bank.all.length + ' 题。答题记录保存在本机，请定期导出备份。', 5200);
          try { localStorage.setItem('ce_study::seenIntro', '1'); } catch (e) { /* ignore */ }
        }, 900);
      }
      /* PWA */
      if ('serviceWorker' in navigator && location.protocol === 'http:' || location.protocol === 'https:') {
        navigator.serviceWorker.register('sw.js').catch(function () { /* 离线已可用，忽略 */ });
      }
    }).catch(function (e) {
      document.getElementById('view').innerHTML =
        '<div class="card"><h2>启动失败</h2><div class="feedback bad">' + UI.esc(e.message || String(e)) + '</div></div>';
    });

    /* 全局事件 */
    document.getElementById('view').addEventListener('click', onClick);
    document.getElementById('view').addEventListener('change', onChange);
    document.getElementById('view').addEventListener('input', onInput);
    document.getElementById('view').addEventListener('change', function (ev) {
      if (ev.target.id === 'fileInput') onFile(ev);
    });
    document.getElementById('nav').addEventListener('click', onClick);
    document.getElementById('btnTheme').addEventListener('click', function () {
      App.state.meta.settings.dark = !App.state.meta.settings.dark;
      App.applyTheme();
      App.save();
      App.render();
    });
    document.addEventListener('keydown', onKey);
    window.addEventListener('beforeunload', function () { App.save(); });
  }

  window.App = App;
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();

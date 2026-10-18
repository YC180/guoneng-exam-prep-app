/* 视图层：首页 / 题库 / 练习 / 错题本 / 模拟考 / 统计 / 资料与设置 */
(function () {
  'use strict';

  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }
  function pct(x) { return x === null || x === undefined ? '—' : Math.round(x * 100) + '%'; }
  function badge(text, cls) { return '<span class="badge ' + (cls || '') + '">' + esc(text) + '</span>'; }
  function statusBadge(q) {
    var s = q.answerStatus || 'missing';
    if (s === 'verified') return badge('已核对', 'ok');
    if (s === 'needs_review') return badge('待核对', 'warn');
    return badge('无答案', 'bad');
  }
  function masteryBadge(r) {
    if (!r || !r.mastery || r.mastery === 'unknown') return '';
    if (r.mastery === 'known') return badge('已掌握', 'ok');
    if (r.mastery === 'vague') return badge('模糊', 'warn');
    return badge('不会', 'bad');
  }
  function bar(ratio, cls) {
    var w = Math.max(0, Math.min(1, ratio || 0)) * 100;
    return '<div class="bar ' + (cls || '') + '"><i style="width:' + w.toFixed(1) + '%"></i></div>';
  }

  /* -------------------------------------------------------- 题目渲染 */
  function renderQuestion(q, ctx) {
    ctx = ctx || {};
    var r = ctx.rec || {};
    var showFeedback = !!ctx.showFeedback;
    var ua = ctx.userAnswer || [];
    var res = ctx.result || null;
    var reviewed = !!ctx.reviewed;
    var h = [];
    h.push('<div class="qmeta">');
    h.push(badge(Bank.typeLabel(q.type), 'accent'));
    h.push(badge(q.category || '未分类'));
    h.push(badge(q.chapter || '未分类'));
    statusBadge(q);
    if ((q.tags || []).indexOf('重点') >= 0) h.push(badge('重点', 'brand'));
    if ((q.tags || []).indexOf('真题') >= 0) h.push(badge('真题', 'brand'));
    if (r.fav) h.push(badge('★ 收藏', 'brand'));
    h.push(masteryBadge(r));
    if (ctx.indexInfo) h.push(badge(ctx.indexInfo));
    h.push('</div>');

    h.push('<div class="stem">' + esc(q.stem) + '</div>');

    if (q.type === 'true_false') {
      var opts = [{ key: '正确', text: '正确' }, { key: '错误', text: '错误' }];
      h.push(optionList(q, opts, ua, res, showFeedback, reviewed));
    } else if (q.options && q.options.length) {
      h.push(optionList(q, q.options, ua, res, showFeedback, reviewed));
    } else {
      if (ctx.inputName) {
        h.push('<label class="field"><span>请作答（填空题：多个空用 / 分隔；简答题请自评）</span>' +
          '<textarea id="' + ctx.inputName + '" placeholder="在此填写你的答案">' + esc((ua || [])[0] || '') + '</textarea></label>');
      }
    }

    if (showFeedback && res) {
      if (res.correct === true) {
        h.push('<div class="feedback ok">回答正确<div class="ans">标准答案：' + esc((q.answer || []).join('、') || '（原资料未提供）') + '</div></div>');
      } else if (res.correct === false) {
        h.push('<div class="feedback bad">回答错误<div class="ans">正确答案：' + esc((q.answer || []).join('、')) +
          '<br>你的答案：' + esc((ua || []).join('、') || '（未作答）') + '</div></div>');
      } else {
        var why = res.reason === 'self-assess' ? '本题为简答/论述题，请对照参考答案自评'
          : (q.answerStatus === 'needs_review' ? '本题标准答案待核对，请回到原资料确认后使用'
            : (res.reason === 'no-answer' ? '原资料未提供标准答案' : '无法自动判分'));
        h.push('<div class="feedback warn">' + esc(why) +
          '<div class="ans">参考答案：' + esc((q.answer || []).join('、') || '（原资料未提供）') +
          '（本题不计入正确率统计）</div></div>');
      }
    }

    if (showFeedback || reviewed) {
      if ((q.explanation || '').trim()) {
        h.push('<div class="expl"><strong>解析：</strong>' + esc(q.explanation) + '</div>');
      } else {
        h.push('<div class="expl muted">原资料未提供解析。APP 不会自动编写解析以免误导。</div>');
      }
      h.push('<div class="src">来源：' + esc(q.sourceFile || '未知') +
        (q.sourcePage ? '（约第 ' + q.sourcePage + ' 页）' : '') + '</div>');
    }
    return h.join('');
  }

  function optionList(q, opts, ua, res, showFeedback, reviewed) {
    var h = [];
    var ansKeys = (q.answer || []).map(function (x) { return String(x).toUpperCase(); });
    opts.forEach(function (o) {
      var key = String(o.key);
      var pressed = ua.indexOf(key) >= 0 || ua.indexOf(key.toUpperCase()) >= 0;
      var cls = 'opt';
      var mk = '';
      if (showFeedback || reviewed) {
        var isAns = ansKeys.indexOf(key.toUpperCase()) >= 0;
        var mine = pressed;
        if (isAns) { cls += ' correct'; mk = '正确答案'; }
        else if (mine) { cls += ' wrong'; mk = '你的答案'; }
      }
      h.push('<button type="button" class="' + cls + '" data-opt="' + esc(key) + '" aria-pressed="' + pressed + '">' +
        '<span class="k">' + esc(key) + '</span><span class="t">' + esc(o.text) + '</span>' +
        (mk ? '<span class="mk">' + mk + '</span>' : '') + '</button>');
    });
    return h.join('');
  }

  /* -------------------------------------------------------- 首页 */
  function viewHome(state) {
    var target = (state.meta && state.meta.targetDate) || '2026-10-24';
    var p = Practice.plan(state, target);
    var o = Stats.overview(state);
    var days = Practice.daysLeft(target);
    var h = [];
    h.push('<div class="card">');
    h.push('<div class="row between"><h2 style="margin:0">距离学习完成目标</h2>' +
      '<span class="muted">目标日 ' + esc(target) + '</span></div>');
    h.push('<div style="font-size:2.3rem;font-weight:750;line-height:1.15;margin:6px 0">' +
      (days >= 0 ? days + ' <span style="font-size:1rem;font-weight:500">天</span>' : '已超过目标日') + '</div>');
    if (days < 0) h.push('<div class="muted">建议在设置中调整目标日期，或按剩余题量重新分配任务。</div>');
    h.push('</div>');

    h.push('<div class="card"><h2>今日任务</h2>');
    h.push('<div class="row between"><span class="muted">计划 ' + p.goal + ' 题（复习 ' + p.goalReview +
      ' + 新题 ' + p.goalNew + '）</span><span>' + p.done + ' / ' + (p.goal || 0) + '</span></div>');
    h.push(bar(p.goal ? p.done / p.goal : 0));
    if (p.behind) {
      h.push('<div class="feedback warn" style="margin-top:10px">按当前进度，剩余 ' + p.remainingDays +
        ' 天需每天完成约 <strong>' + p.perDayNew + '</strong> 道新题才能覆盖全部题库。任务量已相应上调。</div>');
    }
    h.push('<div class="row" style="margin-top:12px">' +
      '<button class="btn-primary btn-big" data-act="today">开始今日学习</button></div>');
    h.push('<div class="row" style="margin-top:8px">' +
      '<button data-act="resume">继续上次学习</button>' +
      '<button data-act="wrong-practice">复习错题</button>' +
      '<button data-act="go-exam">开始模拟考</button>' +
      '<button data-act="due-practice">到期复习 (' + o.due + ')</button>' +
      '</div>');
    h.push('</div>');

    h.push('<div class="card"><h2>学习总览</h2><div class="grid4">');
    h.push(stat(o.total, '题库总量'));
    h.push(stat(o.seen, '已答题数'));
    h.push(stat(o.unseen, '尚未学习'));
    h.push(stat(o.due, '待复习'));
    h.push(stat(o.wrongQ, '错题数'));
    h.push(stat(o.fav, '收藏数'));
    h.push(stat(pct(o.accuracy), '正确率'));
    h.push(stat(pct(o.masteryRate), '掌握率'));
    h.push('</div>');
    h.push('<div class="hint">覆盖率 ' + pct(o.coverage) + '（已答 ' + o.seen + ' / 共 ' + o.total +
      ' 题）。正确率与掌握率均为可验证口径，不代表“保证掌握”。</div>');
    h.push('</div>');

    var weak = Stats.weakPoints(state, 5);
    var stub = Stats.stubborn(state, 5);
    h.push('<div class="card"><h2>今日重点</h2>');
    if (!weak.length && !stub.length) {
      h.push('<div class="muted">还没有足够的作答记录。先开始今日学习，系统会逐步给出薄弱章节与反复做错的题目。</div>');
    }
    if (weak.length) {
      h.push('<h3>错误率最高的章节</h3><table class="tbl"><tr><th>章节</th><th class="num">错题</th><th class="num">正确率</th></tr>');
      weak.forEach(function (w) {
        h.push('<tr><td>' + esc(w.chapter) + '</td><td class="num">' + w.wrong + '</td><td class="num">' + pct(w.rate) + '</td></tr>');
      });
      h.push('</table>');
    }
    if (stub.length) {
      h.push('<h3>反复做错的题目</h3>');
      stub.forEach(function (s) {
        h.push('<button class="qitem" data-open-q="' + esc(s.q.id) + '">' +
          '<div class="hd">' + badge('错 ' + s.times + ' 次', 'bad') + badge(s.q.chapter || '') + '</div>' +
          '<div class="tx">' + esc(s.q.stem) + '</div></button>');
      });
    }
    h.push('</div>');

    var tr = Stats.trend(state, 7);
    h.push('<div class="card"><h2>最近 7 天</h2>');
    h.push(trendChart(tr));
    h.push('<div class="hint">今日已答 ' + p.todayAnswered + ' 题，正确 ' + p.todayCorrect + '，错误 ' + p.todayWrong + '。</div>');
    h.push('</div>');
    return h.join('');
  }

  function stat(v, k) { return '<div class="stat"><div class="v">' + esc(v) + '</div><div class="k">' + esc(k) + '</div></div>'; }

  function trendChart(rows) {
    var max = 1;
    rows.forEach(function (r) { max = Math.max(max, r.answered); });
    var h = ['<div style="display:flex;gap:6px;align-items:flex-end;height:90px">'];
    rows.forEach(function (r) {
      var hpct = Math.round((r.answered / max) * 100);
      var okpct = r.answered ? Math.round((r.correct / r.answered) * 100) : 0;
      h.push('<div style="flex:1;display:flex;flex-direction:column;justify-content:flex-end;align-items:center;height:100%">' +
        '<div title="' + r.answered + ' 题" style="width:100%;background:var(--accent-soft);border-radius:6px;height:' + hpct + '%;display:flex;align-items:flex-end;position:relative;min-height:2px">' +
        '<div style="width:100%;height:' + okpct + '%;background:var(--ok);border-radius:6px"></div></div>' +
        '<div class="small muted" style="margin-top:4px">' + esc(r.label) + '</div>' +
        '<div class="small" style="font-variant-numeric:tabular-nums">' + r.answered + '</div>' +
        '</div>');
    });
    h.push('</div>');
    return h.join('');
  }

  /* -------------------------------------------------------- 题库 */
  var bankFilter = { keyword: '', category: '', chapter: '', type: '', tag: '', status: '', sort: 'default' };

  function viewBank(state, params) {
    params = params || {};
    if (params.reset) { bankFilter = { keyword: '', category: '', chapter: '', type: '', tag: '', status: '', sort: 'default' }; }
    if (params.category !== undefined) { bankFilter.category = params.category; bankFilter.chapter = ''; }
    if (params.chapter !== undefined) bankFilter.chapter = params.chapter;
    if (params.tag !== undefined) bankFilter.tag = params.tag;

    var list = Bank.filter(bankFilter);
    list = Bank.sort(list, bankFilter.sort, state.progress);
    var page = params.page || 0;
    var per = 30;
    var slice = list.slice(page * per, page * per + per);
    var h = [];

    h.push('<div class="card tight">');
    h.push('<label class="field"><span>搜索题干 / 选项 / 解析</span>' +
      '<input type="search" id="bankKw" placeholder="输入关键词，空格分隔多个词" value="' + esc(bankFilter.keyword) + '"></label>');
    h.push('<div class="row"><select id="bankCat"><option value="">全部资料类别（' + Bank.all.length + ' 题）</option>');
    Bank.facets.categories.forEach(function (c) {
      h.push('<option value="' + esc(c.name) + '"' + (bankFilter.category === c.name ? ' selected' : '') + '>' +
        esc(c.name) + '（' + c.count + '）</option>');
    });
    h.push('</select>');
    if (bankFilter.category && Bank.facets.chapters[bankFilter.category]) {
      h.push('<select id="bankCh"><option value="">全部章节</option>');
      var chs = Bank.facets.chapters[bankFilter.category];
      Object.keys(chs).sort(function (a, b) { return chs[b] - chs[a]; }).forEach(function (c) {
        h.push('<option value="' + esc(c) + '"' + (bankFilter.chapter === c ? ' selected' : '') + '>' + esc(c) + '（' + chs[c] + '）</option>');
      });
      h.push('</select>');
    }
    h.push('<select id="bankType"><option value="">全部题型</option>');
    Bank.facets.types.forEach(function (t) {
      h.push('<option value="' + esc(t.name) + '"' + (bankFilter.type === t.name ? ' selected' : '') + '>' + esc(t.label) + '（' + t.count + '）</option>');
    });
    h.push('</select>');
    h.push('<select id="bankStatus"><option value="">全部状态</option>' +
      '<option value="verified"' + (bankFilter.status === 'verified' ? ' selected' : '') + '>已核对</option>' +
      '<option value="needs_review"' + (bankFilter.status === 'needs_review' ? ' selected' : '') + '>待核对</option>' +
      '<option value="missing"' + (bankFilter.status === 'missing' ? ' selected' : '') + '>无答案</option>' +
      '</select>');
    h.push('<select id="bankSort">' +
      opt('default', '原始顺序', bankFilter.sort) + opt('new', '未学习优先', bankFilter.sort) +
      opt('wrong', '错误次数多优先', bankFilter.sort) + opt('rate', '正确率低优先', bankFilter.sort) +
      opt('recent', '最近学习优先', bankFilter.sort) + '</select>');
    h.push('<button class="btn-sm" data-act="bank-reset">重置筛选</button>');
    h.push('</div>');
    h.push('<div class="row" style="margin-top:8px">' +
      '<span class="muted">共 ' + list.length + ' 题' + (list.length > per ? '，第 ' + (page + 1) + ' / ' + Math.ceil(list.length / per) + ' 页' : '') + '</span>' +
      '<button class="btn-sm btn-accent" data-act="bank-practice">用当前筛选结果练习</button>' +
      '</div>');
    if (Bank.facets.tags.length) {
      h.push('<div class="chips" style="margin-top:8px">');
      Bank.facets.tags.forEach(function (t) {
        h.push('<button class="chip tag' + (t.name === '重点' || t.name === '真题' ? ' hot' : '') +
          '" data-tag="' + esc(t.name) + '" aria-pressed="' + (bankFilter.tag === t.name) + '">' + esc(t.name) + '（' + t.count + '）</button>');
      });
      h.push('</div>');
    }
    h.push('</div>');

    if (!slice.length) {
      h.push('<div class="empty"><div class="big">🔍</div><div>没有符合条件的题目。</div>' +
        '<div class="muted">可以放宽筛选条件，或在“资料与设置”中导入自己的题库。</div></div>');
      return h.join('');
    }
    slice.forEach(function (q) {
      var r = Practice.rec(state.progress, q.id);
      h.push('<button class="qitem" data-open-q="' + esc(q.id) + '">' +
        '<div class="hd">' + badge(Bank.typeLabel(q.type), 'accent') + badge(q.chapter || '') +
        statusBadge(q) + (r.fav ? badge('★', 'brand') : '') +
        (r.wrongCount ? badge('错 ' + r.wrongCount + ' 次', 'bad') : '') +
        (r.seen && !r.wrongCount ? badge('已练习', 'ok') : '') + '</div>' +
        '<div class="tx">' + esc(q.stem) + '</div></button>');
    });

    if (list.length > per) {
      h.push('<div class="row center" style="justify-content:center">' +
        '<button class="btn-sm" data-page="' + (page - 1) + '"' + (page <= 0 ? ' disabled' : '') + '>上一页</button>' +
        '<button class="btn-sm" data-page="' + (page + 1) + '"' +
        (page + 1 >= Math.ceil(list.length / per) ? ' disabled' : '') + '>下一页</button></div>');
    }
    return h.join('');
  }

  function opt(v, label, cur) {
    return '<option value="' + esc(v) + '"' + (cur === v ? ' selected' : '') + '>' + esc(label) + '</option>';
  }

  /* -------------------------------------------------------- 题目详情 */
  function viewQuestion(state, params) {
    var q = Bank.byId[params.qid];
    if (!q) return '<div class="empty">题目不存在。</div>';
    var r = Practice.rec(state.progress, q.id);
    var h = [];
    h.push('<div class="card">');
    h.push(renderQuestion(q, {
      rec: r, reviewed: true, showFeedback: true,
      userAnswer: r.lastAnswer || [], result: Practice.judge(q, r.lastAnswer || []),
      indexInfo: (r.seen ? '已作答 ' + r.seen + ' 次' : '尚未作答'),
    }));
    h.push('<div class="row" style="margin-top:10px">' +
      '<button data-act="fav" data-qid="' + esc(q.id) + '">' + (r.fav ? '取消收藏' : '☆ 收藏') + '</button>' +
      '<button data-act="mastery" data-level="known" data-qid="' + esc(q.id) + '">标记已掌握</button>' +
      '<button data-act="mastery" data-level="vague" data-qid="' + esc(q.id) + '">标记模糊</button>' +
      '<button data-act="mastery" data-level="unknown" data-qid="' + esc(q.id) + '">标记不会</button>' +
      '</div>');
    h.push('<label class="field" style="margin-top:10px"><span>错因记录（可选）</span>' +
      '<input type="text" id="wrongReason" value="' + esc(r.wrongReason || '') + '" placeholder="如：概念记混 / 计算失误 / 审题不清"></label>');
    h.push('<button class="btn-sm" data-act="save-reason" data-qid="' + esc(q.id) + '">保存错因</button>');
    if (state.wrongBook[q.id]) {
      h.push('<button class="btn-sm" data-act="remove-wrong" data-qid="' + esc(q.id) + '">从错题本移除</button>');
    }
    h.push('<div class="row" style="margin-top:12px">' +
      '<button class="btn-accent" data-act="practice-one" data-qid="' + esc(q.id) + '">单题练习</button>' +
      '<button data-act="bank-back">返回题库</button></div>');
    h.push('</div>');
    h.push('<div class="card"><h2>历史记录</h2><div class="kv">' +
      '<dt>作答次数</dt><dd>' + (r.seen || 0) + '</dd>' +
      '<dt>答对 / 答错</dt><dd>' + (r.correctCount || 0) + ' / ' + (r.wrongCount || 0) + '</dd>' +
      '<dt>掌握程度</dt><dd>' + ({ known: '已掌握', vague: '模糊', unknown: '不会' }[r.mastery] || '未标记') + '</dd>' +
      '<dt>下次复习</dt><dd>' + (r.reviewDue ? new Date(r.reviewDue).toLocaleDateString('zh-CN') : '—') + '</dd>' +
      '<dt>错题本次数</dt><dd>' + (state.wrongBook[q.id] || 0) + '</dd>' +
      '</div></div>');
    return h.join('');
  }

  /* -------------------------------------------------------- 练习 */
  var practiceStart = { mode: 'sequential', limit: 30, category: '', chapter: '' };

  function viewPractice(state) {
    var s = state.session;
    if (s && s.queue && s.queue.length) return viewPracticeRunner(state, s);
    return viewPracticeSetup(state);
  }

  function viewPracticeSetup(state) {
    var h = [];
    h.push('<div class="card"><h2>选择练习方式</h2>');
    h.push('<div class="chips">');
    var modes = [
      ['sequential', '顺序刷题'], ['random', '随机刷题'], ['new', '只练未学习'],
      ['wrong', '只练错题'], ['fav', '只练收藏'], ['due', '只练到期复习'],
      ['weak', '只练薄弱题'], ['chapter', '按章节专项'],
    ];
    modes.forEach(function (m) {
      h.push('<button class="chip" data-pmode="' + m[0] + '" aria-pressed="' + (practiceStart.mode === m[0]) + '">' + m[1] + '</button>');
    });
    h.push('</div>');
    h.push('<div class="row" style="margin-top:12px"><label class="field" style="flex:1;margin:0"><span>题量</span>' +
      '<input type="number" id="pLimit" min="1" max="500" value="' + practiceStart.limit + '"></label></div>');
    h.push('<div class="row" style="margin-top:10px"><select id="pCat"><option value="">全部资料类别</option>');
    Bank.facets.categories.forEach(function (c) {
      h.push('<option value="' + esc(c.name) + '"' + (practiceStart.category === c.name ? ' selected' : '') + '>' + esc(c.name) + '（' + c.count + '）</option>');
    });
    h.push('</select>');
    if (practiceStart.category && Bank.facets.chapters[practiceStart.category]) {
      h.push('<select id="pCh"><option value="">全部章节</option>');
      var chs = Bank.facets.chapters[practiceStart.category];
      Object.keys(chs).sort(function (a, b) { return chs[b] - chs[a]; }).forEach(function (c) {
        h.push('<option value="' + esc(c) + '"' + (practiceStart.chapter === c ? ' selected' : '') + '>' + esc(c) + '（' + chs[c] + '）</option>');
      });
      h.push('</select>');
    }
    h.push('</div>');
    h.push('<div class="hint">练习模式答完即可看答案与解析；模拟考试默认交卷后统一显示。</div>');
    h.push('<button class="btn-primary btn-big" style="margin-top:12px" data-act="p-start">开始练习</button>');
    h.push('</div>');

    h.push('<div class="card"><h2>题量概览</h2><div class="grid3">');
    h.push(stat(Bank.all.length, '题库总量'));
    h.push(stat(Practice.poolNew(state).length, '未学习'));
    h.push(stat(Object.keys(state.wrongBook || {}).length, '错题本'));
    h.push(stat(Practice.poolFav(state).length, '收藏'));
    h.push(stat(Practice.poolDue(state).length, '到期复习'));
    h.push(stat(Practice.poolWeak(state).length, '薄弱题'));
    h.push('</div></div>');
    return h.join('');
  }

  function buildPool(state, mode, opts) {
    var pool;
    switch (mode) {
      case 'new': pool = Practice.poolNew(state); break;
      case 'wrong': pool = Practice.poolWrong(state); break;
      case 'fav': pool = Practice.poolFav(state); break;
      case 'due': pool = Practice.poolDue(state); break;
      case 'weak': pool = Practice.poolWeak(state); break;
      default: pool = Bank.filter({ category: opts.category, chapter: opts.chapter });
    }
    if (mode === 'chapter' || mode === 'sequential' || mode === 'random') {
      pool = Bank.filter({ category: opts.category, chapter: opts.chapter });
    }
    if (mode === 'random' || mode === 'sequential') {
      /* 未指定章节时使用全库 */
      if (!opts.category && !opts.chapter) pool = Bank.all.slice();
    }
    return pool || [];
  }

  function startPractice(state, mode, opts) {
    opts = opts || {};
    var pool = buildPool(state, mode, opts);
    var limit = opts.limit || 30;
    var list = Bank.pick({ pool: pool, shuffle: mode !== 'sequential', limit: limit });
    if (mode === 'sequential' && !opts.shuffle) list = Bank.sort(list, 'default', state.progress).slice(0, limit);
    state.session = {
      mode: mode, title: modeLabel(mode), queue: list.map(function (q) { return q.id; }),
      idx: 0, submitted: {}, ua: {}, result: {}, startedAt: Date.now(),
      category: opts.category || '', chapter: opts.chapter || '',
    };
    App.persistSession();
    return state.session;
  }

  function modeLabel(m) {
    return {
      sequential: '顺序练习', random: '随机练习', new: '未学习题', wrong: '错题练习',
      fav: '收藏练习', due: '到期复习', weak: '薄弱题练习', chapter: '章节专项',
      today: '今日学习', one: '单题练习',
    }[m] || '练习';
  }

  function viewPracticeRunner(state, s) {
    var q = Bank.byId[s.queue[s.idx]];
    if (!q) {
      return '<div class="card"><div class="empty">练习已结束。<br><button class="btn-primary" data-act="p-finish">返回练习首页</button></div></div>';
    }
    var submitted = !!s.submitted[q.id];
    var ua = s.ua[q.id] || [];
    var res = s.result[q.id] || null;
    var r = Practice.rec(state.progress, q.id);
    var h = [];
    h.push('<div class="card tight"><div class="row between">' +
      '<span class="muted">' + esc(s.title) + ' · 第 ' + (s.idx + 1) + ' / ' + s.queue.length + ' 题</span>' +
      '<button class="btn-sm" data-act="p-quit">退出</button></div>' +
      bar((s.idx + 1) / s.queue.length) + '</div>');

    h.push('<div class="card" id="qcard">');
    h.push(renderQuestion(q, {
      rec: r, showFeedback: submitted, userAnswer: ua, result: res,
      inputName: (q.options && q.options.length) || q.type === 'true_false' ? null : 'qInput',
      indexInfo: '第 ' + (s.idx + 1) + ' 题',
    }));
    h.push('</div>');

    h.push('<div class="card tight">');
    if (!submitted) {
      h.push('<button class="btn-primary btn-big" data-act="p-submit">提交答案</button>');
    } else {
      h.push('<div class="row" style="margin-bottom:8px">' +
        '<button data-act="p-fav" data-qid="' + esc(q.id) + '">' + (r.fav ? '取消收藏' : '☆ 收藏') + '</button>' +
        '<button data-act="p-mastery" data-level="known" data-qid="' + esc(q.id) + '">已掌握</button>' +
        '<button data-act="p-mastery" data-level="vague" data-qid="' + esc(q.id) + '">模糊</button>' +
        '<button data-act="p-mastery" data-level="unknown" data-qid="' + esc(q.id) + '">不会</button>' +
        '</div>');
      h.push('<div class="row">' +
        '<button data-act="p-prev"' + (s.idx <= 0 ? ' disabled' : '') + '>上一题</button>' +
        '<button class="btn-accent btn-big" style="flex:1" data-act="p-next">' +
        (s.idx + 1 >= s.queue.length ? '完成练习' : '下一题') + '</button></div>');
    }
    h.push('<div class="hint">电脑端快捷键：A/B/C/D 选择选项，Enter 提交或下一题，Esc 退出。</div>');
    h.push('</div>');
    return h.join('');
  }

  /* -------------------------------------------------------- 错题本 */
  var wrongFilter = { sort: 'times', chapter: '', reason: '' };

  function viewWrong(state) {
    var wb = state.wrongBook || {};
    var ids = Object.keys(wb);
    var list = ids.map(function (id) { return Bank.byId[id]; }).filter(Boolean);
    if (wrongFilter.chapter) list = list.filter(function (q) { return q.chapter === wrongFilter.chapter; });
    if (wrongFilter.reason) {
      list = list.filter(function (q) {
        var r = state.progress[q.id] || {};
        return (r.wrongReason || '未记录') === wrongFilter.reason;
      });
    }
    if (wrongFilter.sort === 'times') list.sort(function (a, b) { return (wb[b.id] || 0) - (wb[a.id] || 0); });
    else if (wrongFilter.sort === 'recent') list.sort(function (a, b) {
      return ((state.progress[b.id] || {}).lastAt || 0) - ((state.progress[a.id] || {}).lastAt || 0);
    });
    else list.sort(function (a, b) { return (a.chapter || '').localeCompare(b.chapter || '', 'zh'); });

    var h = [];
    var reasons = Stats.wrongReasonStats(state);
    var chapters = {};
    ids.forEach(function (id) {
      var q = Bank.byId[id];
      if (q) chapters[q.chapter || '未分类'] = (chapters[q.chapter || '未分类'] || 0) + 1;
    });
    var due = Practice.poolDue(state).filter(function (q) { return wb[q.id]; }).length;

    h.push('<div class="card tight"><div class="grid3">' +
      stat(ids.length, '错题总数') + stat(due, '今日到期') +
      stat(Practice.poolFav(state).length, '收藏题') + '</div>');
    h.push('<div class="row" style="margin-top:10px">' +
      '<button class="btn-primary" data-act="w-practice">开始错题复习</button>' +
      '<button data-act="w-due">复习今日到期错题</button>' +
      '<button data-act="w-clear">清空错题本</button></div></div>');

    h.push('<div class="card tight"><div class="row">' +
      '<select id="wSort">' + opt('times', '按错误次数', wrongFilter.sort) +
      opt('recent', '按最近错误', wrongFilter.sort) + opt('chapter', '按章节', wrongFilter.sort) + '</select>' +
      '<select id="wChapter"><option value="">全部章节</option>');
    Object.keys(chapters).sort(function (a, b) { return chapters[b] - chapters[a]; }).forEach(function (c) {
      h.push('<option value="' + esc(c) + '"' + (wrongFilter.chapter === c ? ' selected' : '') + '>' + esc(c) + '（' + chapters[c] + '）</option>');
    });
    h.push('</select>');
    h.push('<select id="wReason"><option value="">全部错因</option>');
    reasons.forEach(function (r) {
      h.push('<option value="' + esc(r.reason) + '"' + (wrongFilter.reason === r.reason ? ' selected' : '') + '>' + esc(r.reason) + '（' + r.count + '）</option>');
    });
    h.push('</select></div></div>');

    if (!list.length) {
      h.push('<div class="empty"><div class="big">🎉</div><div>错题本是空的。</div>' +
        '<div class="muted">练习中答错的题目会自动进入错题本。</div></div>');
      return h.join('');
    }
    list.forEach(function (q) {
      var r = Practice.rec(state.progress, q.id);
      h.push('<button class="qitem" data-open-q="' + esc(q.id) + '">' +
        '<div class="hd">' + badge('错 ' + (wb[q.id] || 0) + ' 次', 'bad') + badge(q.chapter || '') +
        badge(Bank.typeLabel(q.type), 'accent') + statusBadge(q) +
        (r.wrongReason ? badge(r.wrongReason, 'warn') : '') +
        (r.reviewDue && r.reviewDue <= Date.now() ? badge('到期', 'brand') : '') + '</div>' +
        '<div class="tx">' + esc(q.stem) + '</div></button>');
    });
    return h.join('');
  }

  /* -------------------------------------------------------- 模拟考 */
  var examSetup = { count: 100, duration: 60, category: '', chapter: '' };

  function viewExam(state) {
    if (state.currentExam) return viewExamRunner(state, state.currentExam);
    if (state.examResult) return viewExamResult(state, state.examResult);
    var h = [];
    var avail = Bank.all.filter(function (q) {
      return (q.type === 'single_choice' || q.type === 'multiple_choice' || q.type === 'true_false');
    }).length;
    h.push('<div class="card"><h2>创建试卷</h2>');
    h.push('<div class="row"><label class="field" style="flex:1;margin:0"><span>题量</span>' +
      '<input type="number" id="eCount" min="5" max="300" value="' + examSetup.count + '"></label>' +
      '<label class="field" style="flex:1;margin:0"><span>时长（分钟）</span>' +
      '<input type="number" id="eDur" min="5" max="300" value="' + examSetup.duration + '"></label></div>');
    h.push('<div class="row" style="margin-top:10px"><select id="eCat"><option value="">全部资料类别</option>');
    Bank.facets.categories.forEach(function (c) {
      h.push('<option value="' + esc(c.name) + '"' + (examSetup.category === c.name ? ' selected' : '') + '>' + esc(c.name) + '（' + c.count + '）</option>');
    });
    h.push('</select>');
    if (examSetup.category && Bank.facets.chapters[examSetup.category]) {
      h.push('<select id="eCh"><option value="">全部章节</option>');
      var chs = Bank.facets.chapters[examSetup.category];
      Object.keys(chs).sort(function (a, b) { return chs[b] - chs[a]; }).forEach(function (c) {
        h.push('<option value="' + esc(c) + '"' + (examSetup.chapter === c ? ' selected' : '') + '>' + esc(c) + '（' + chs[c] + '）</option>');
      });
      h.push('</select>');
    }
    h.push('</div>');
    h.push('<div class="hint">可参与模拟考（单选/多选/判断）的题目共 ' + avail + ' 道。默认交卷后统一显示答案与解析。</div>');
    h.push('<label class="row" style="margin-top:8px"><input type="checkbox" id="eLive"> <span class="muted">作答后立即显示本题答案（默认关闭）</span></label>');
    h.push('<button class="btn-primary btn-big" style="margin-top:12px" data-act="e-start">开始考试</button>');
    h.push('</div>');

    var past = state.exams || [];
    h.push('<div class="card"><h2>历史成绩</h2>');
    if (!past.length) h.push('<div class="muted">还没有考试记录。</div>');
    else {
      h.push('<div class="scrollx"><table class="tbl"><tr><th>时间</th><th>范围</th><th class="num">得分</th><th class="num">用时</th><th></th></tr>');
      past.slice(0, 20).forEach(function (e) {
        h.push('<tr><td>' + new Date(e.submittedAt || e.createdAt).toLocaleString('zh-CN') + '</td>' +
          '<td>' + esc(e.scope || '') + '</td>' +
          '<td class="num">' + (e.result ? e.result.score + ' 分' : '—') + '</td>' +
          '<td class="num">' + (e.result ? Exam.fmt(e.result.elapsedSec) : '—') + '</td>' +
          '<td><button class="btn-sm" data-act="e-review" data-eid="' + esc(e.id) + '">回顾</button></td></tr>');
      });
      h.push('</table></div>');
    }
    h.push('</div>');
    return h.join('');
  }

  function viewExamRunner(state, exam) {
    var i = exam.cursor || 0;
    var q = Bank.byId[exam.qids[i]];
    var h = [];
    var rem = Exam.remaining(exam);
    var answered = Object.keys(exam.answers).filter(function (k) {
      return exam.answers[k] && exam.answers[k].length;
    }).length;
    h.push('<div class="card tight"><div class="row between">' +
      '<span class="muted">' + esc(exam.title) + '</span>' +
      '<span class="timer' + (rem < 300 ? ' low' : '') + '" id="examTimer">' + Exam.fmt(rem) + '</span></div>' +
      '<div class="row between" style="margin-top:6px"><span class="muted">已答 ' + answered + ' / ' + exam.qids.length + '</span>' +
      '<button class="btn-sm btn-primary" data-act="e-submit">交卷</button></div>' +
      '</div>');
    h.push('<div class="card tight"><div class="row between"><span class="muted">第 ' + (i + 1) + ' / ' + exam.qids.length + ' 题</span>' +
      '<button class="btn-sm" data-act="e-card">答题卡</button></div>' + bar((i + 1) / exam.qids.length) + '</div>');
    if (!q) return h.join('<div class="empty">题目缺失</div>');
    h.push('<div class="card">');
    var showAns = exam.showAnswerPerQuestion && (exam.answers[q.id] || []).length;
    h.push(renderQuestion(q, {
      rec: Practice.rec(state.progress, q.id),
      showFeedback: showAns,
      userAnswer: exam.answers[q.id] || [],
      result: showAns ? Practice.judge(q, exam.answers[q.id] || []) : null,
    }));
    h.push('</div>');
    h.push('<div class="card tight"><div class="row">' +
      '<button data-act="e-prev"' + (i <= 0 ? ' disabled' : '') + '>上一题</button>' +
      '<button class="btn-sm" data-act="e-flag" data-qid="' + esc(q.id) + '">' +
      (exam.flagged[q.id] ? '取消标记' : '标记待查') + '</button>' +
      '<button class="btn-accent btn-big" style="flex:1" data-act="e-next">' +
      (i + 1 >= exam.qids.length ? '最后一题' : '下一题') + '</button></div></div>');

    if (exam.showCard) {
      h.push('<div class="card"><h2>答题卡</h2><div class="anscard">');
      exam.qids.forEach(function (qid, idx) {
        var a = exam.answers[qid] || [];
        var cls = a.length ? 'done' : '';
        if (idx === i) cls += ' cur';
        if (exam.flagged[qid]) cls += ' err';
        h.push('<button class="' + cls + '" data-act="e-goto" data-idx="' + idx + '">' + (idx + 1) + '</button>');
      });
      h.push('</div><div class="hint">蓝色=已作答，红框=已标记，粗框=当前题。</div></div>');
    }
    return h.join('');
  }

  function viewExamResult(state, result) {
    var exam = result.exam;
    var r = result.result;
    var h = [];
    h.push('<div class="card"><h2>成绩</h2>');
    h.push('<div class="grid3">' + stat(r.score + ' 分', '得分率') +
      stat(r.correct + ' / ' + r.scored, '答对 / 可判分') +
      stat(Exam.fmt(r.elapsedSec), '用时') + '</div>');
    h.push('<div class="kv" style="margin-top:10px">' +
      '<dt>题目总数</dt><dd>' + r.total + '</dd>' +
      '<dt>未作答</dt><dd>' + r.unanswered + '</dd>' +
      '<dt>答错</dt><dd>' + r.wrong + '</dd>' +
      '<dt>待核对（不计分）</dt><dd>' + r.unverified + '</dd></div>');
    h.push('<div class="hint">得分率仅按“已核对且有答案”的题计算，待核对题目不计入，避免误导。</div>');
    h.push('<div class="row" style="margin-top:10px">' +
      '<button class="btn-primary" data-act="e-again">再考一次</button>' +
      '<button data-act="e-back">返回模拟考</button></div></div>');

    var rank = Exam.chapterRank(r);
    h.push('<div class="card"><h2>章节分析（由弱到强）</h2><div class="scrollx"><table class="tbl">' +
      '<tr><th>章节</th><th class="num">题量</th><th class="num">对</th><th class="num">错</th><th class="num">未答</th><th class="num">正确率</th></tr>');
    rank.forEach(function (x) {
      h.push('<tr><td>' + esc(x.chapter) + '</td><td class="num">' + x.total + '</td>' +
        '<td class="num">' + x.correct + '</td><td class="num">' + x.wrong + '</td>' +
        '<td class="num">' + (x.blank || 0) + '</td>' +
        '<td class="num">' + pct(x.rate) + '</td></tr>');
    });
    h.push('</table></div><div class="hint">“错”含未作答（考试中未作答同样不得分）；未作答的题目不会计入错题本。</div></div>');

    h.push('<div class="card"><h2>题目回顾</h2>');
    exam.qids.forEach(function (qid, idx) {
      var q = Bank.byId[qid];
      if (!q) return;
      var d = r.detail[idx] || {};
      var cls = d.correct === true ? 'ok' : (d.correct === false ? 'bad' : 'warn');
      var label = d.correct === true ? '正确'
        : (d.answered === false ? '未作答' : (d.correct === false ? '错误' : '待核对'));
      h.push('<details class="acc"><summary>' +
        '<span class="badge ' + cls + '">' + label + '</span> ' +
        '第 ' + (idx + 1) + ' 题 · ' + esc(q.chapter || '') + '</summary>');
      h.push(renderQuestion(q, {
        rec: Practice.rec(state.progress, q.id), reviewed: true, showFeedback: true,
        userAnswer: d.userAnswer || [], result: Practice.judge(q, d.userAnswer || []),
      }));
      h.push('</details>');
    });
    h.push('</div>');
    return h.join('');
  }

  /* -------------------------------------------------------- 统计 */
  function viewStats(state) {
    var o = Stats.overview(state);
    var h = [];
    h.push('<div class="card"><h2>总体</h2><div class="grid4">' +
      stat(o.total, '题库总量') + stat(o.seen, '已答题数') + stat(o.unseen, '未学习') +
      stat(o.due, '待复习') + stat(pct(o.accuracy), '正确率') +
      stat(pct(o.coverage), '覆盖率') + stat(pct(o.masteryRate), '掌握率') +
      stat(o.attempts, '累计作答') + '</div>');
    h.push('<div class="hint">答对 ' + o.correct + ' 次，答错 ' + o.wrong + ' 次；待核对题目作答 ' + o.unverified + ' 次（未计入正确率）。</div>');
    h.push('</div>');

    var tr = Stats.trend(state, 14);
    h.push('<div class="card"><h2>近 14 天趋势</h2>' + trendChart(tr));
    h.push('<div class="scrollx"><table class="tbl"><tr><th>日期</th><th class="num">答题</th><th class="num">正确</th><th class="num">错误</th><th class="num">用时(分)</th></tr>');
    tr.slice().reverse().forEach(function (x) {
      h.push('<tr><td>' + esc(x.date) + '</td><td class="num">' + x.answered + '</td>' +
        '<td class="num">' + x.correct + '</td><td class="num">' + x.wrong + '</td>' +
        '<td class="num">' + (x.minutes || 0) + '</td></tr>');
    });
    h.push('</table></div></div>');

    var rows = Stats.byChapter(state);
    h.push('<div class="card"><h2>章节正确率与掌握率（由弱到强）</h2><div class="scrollx"><table class="tbl">' +
      '<tr><th>章节</th><th class="num">题量</th><th class="num">已答</th><th class="num">正确率</th><th class="num">已掌握</th></tr>');
    rows.forEach(function (x) {
      h.push('<tr><td>' + esc(x.chapter) + '</td><td class="num">' + x.total + '</td>' +
        '<td class="num">' + x.seen + '</td><td class="num">' + pct(x.rate) + '</td>' +
        '<td class="num">' + x.mastered + '</td></tr>');
    });
    h.push('</table></div></div>');

    var weak = Stats.weakPoints(state, 10);
    h.push('<div class="card"><h2>易错知识点</h2>');
    if (!weak.length) h.push('<div class="muted">暂无数据。</div>');
    else {
      h.push('<div class="scrollx"><table class="tbl"><tr><th>章节</th><th class="num">错题</th><th class="num">正确率</th></tr>');
      weak.forEach(function (w) {
        h.push('<tr><td>' + esc(w.chapter) + '</td><td class="num">' + w.wrong + '</td><td class="num">' + pct(w.rate) + '</td></tr>');
      });
      h.push('</table></div>');
    }
    h.push('</div>');

    var reasons = Stats.wrongReasonStats(state);
    h.push('<div class="card"><h2>错因分布</h2>');
    if (!reasons.length) h.push('<div class="muted">暂无错因记录。可在题目详情中记录错因。</div>');
    else {
      h.push('<div class="scrollx"><table class="tbl"><tr><th>错因</th><th class="num">题数</th></tr>');
      reasons.forEach(function (x) { h.push('<tr><td>' + esc(x.reason) + '</td><td class="num">' + x.count + '</td></tr>'); });
      h.push('</table></div>');
    }
    h.push('</div>');
    return h.join('');
  }

  /* -------------------------------------------------------- 资料与设置 */
  function viewMore(state) {
    var K = window.CE_KNOWLEDGE || {};
    var meta = state.meta || {};
    var st = meta.settings || {};
    var h = [];

    h.push('<div class="card"><h2>目标与偏好</h2>');
    h.push('<label class="field"><span>学习完成目标日期（默认 2026-10-24）</span>' +
      '<input type="date" id="setTarget" value="' + esc(meta.targetDate || '2026-10-24') + '"></label>');
    h.push('<label class="field"><span>每日新题上限（0 表示不限制，由剩余天数自动计算）</span>' +
      '<input type="number" id="setDailyNew" min="0" max="500" value="' + (st.dailyNew || 0) + '"></label>');
    h.push('<label class="field"><span>字号</span><select id="setFont">' +
      opt('1', '标准', String(st.fontScale || 1)) + opt('1.12', '大', String(st.fontScale || 1)) +
      opt('1.25', '特大', String(st.fontScale || 1)) + '</select></label>');
    h.push('<label class="row"><input type="checkbox" id="setDark"' + (st.dark ? ' checked' : '') + '> <span class="muted">深色模式</span></label>');
    h.push('<label class="row" style="margin-top:6px"><input type="checkbox" id="setOnePer"' + (st.onePerScreen !== false ? ' checked' : '') + '> <span class="muted">一题一屏（练习时隐藏其他内容）</span></label>');
    h.push('<button class="btn-primary" style="margin-top:12px" data-act="save-settings">保存设置</button>');
    h.push('</div>');

    h.push('<div class="card"><h2>题库与数据</h2>');
    h.push('<div class="kv"><dt>内置题库</dt><dd>' + (Bank.loadInfo.builtin || 0) + ' 题</dd>' +
      '<dt>导入题库</dt><dd>' + (Bank.loadInfo.imported || 0) + ' 题</dd>' +
      '<dt>题库生成日期</dt><dd>' + esc(Bank.loadInfo.generatedAt || '—') + '</dd>' +
      '<dt>存储方式</dt><dd>' + (Store.backendName() === 'idb' ? 'IndexedDB（推荐）' :
        Store.backendName() === 'ls' ? 'localStorage（容量较小，建议用 start.cmd 以 http 打开）' : '内存（关闭页面会丢失）') + '</dd></div>');
    h.push('<div class="row" style="margin-top:12px">' +
      '<button data-act="exp-progress">导出学习记录</button>' +
      '<button data-act="exp-bank">导出题库</button>' +
      '<button class="btn-accent" data-act="exp-backup">导出完整备份</button>' +
      '<button data-act="exp-valid">导出题库校验报告</button>' +
      '<button data-act="tpl">下载题库导入模板</button>' +
      '</div>');
    h.push('<div class="row" style="margin-top:8px">' +
      '<button data-act="imp">导入题库 / 备份（JSON、CSV）</button>' +
      '<button data-act="validate">立即校验题库并查看结果</button>' +
      '</div>');
    h.push('<input type="file" id="fileInput" accept=".json,.csv,.txt" style="display:none">');
    h.push('<div id="impPreview"></div>');
    h.push('</div>');

    h.push('<div class="card"><h2>已核实知识点（联网更新）</h2>');
    if (!K.company) h.push('<div class="muted">未加载 knowledge.js。</div>');
    else {
      h.push('<div class="hint">核实日期：' + esc(K.verifiedAt) + '。来源：' +
        (K.sources || []).map(function (s) { return '<a href="' + esc(s.url) + '" target="_blank" rel="noopener">' + esc(s.name) + '</a>'; }).join('、') + '</div>');
      h.push('<details class="acc"><summary>集团概况（2026 官方口径）</summary><dl class="kv">');
      var c = K.company;
      [['全称', c.fullName], ['简称 / 英文', c.shortName + ' / ' + c.enShort], ['挂牌', c.founded],
       ['重组来源', c.origin], ['世界500强', c.fortune500], ['总资产', c.assets], ['员工', c.staff],
       ['定位', c.positioning], ['煤炭产能', c.coalCapacity], ['发电装机', c.powerCapacity],
       ['铁路', c.railway], ['港口', c.port], ['化工', c.chemical], ['上市公司', c.listed],
       ['布局', c.coverage], ['考核', c.award]].forEach(function (kv) {
        h.push('<dt>' + esc(kv[0]) + '</dt><dd>' + esc(kv[1]) + '</dd>');
      });
      h.push('</dl><div class="hint">占比：' + (c.shares || []).map(function (s) { return s[0] + s[1]; }).join('；') + '</div></details>');

      h.push('<details class="acc"><summary>集团领导（官网 2026-10-18）</summary><table class="tbl">');
      (K.leaders.list || []).forEach(function (l) {
        h.push('<tr><td>' + esc(l[0]) + '</td><td>' + esc(l[1]) + '</td></tr>');
      });
      h.push('</table></details>');

      h.push('<details class="acc"><summary>企业文化核心理念（2025 官网新版）</summary><table class="tbl">');
      (K.culture.core || []).forEach(function (kv) {
        h.push('<tr><td style="white-space:nowrap">' + esc(kv[0]) + '</td><td>' + esc(kv[1]) + '</td></tr>');
      });
      h.push('</table><h3>发展理念</h3><table class="tbl">');
      (K.culture.develop || []).forEach(function (kv) {
        h.push('<tr><td style="white-space:nowrap">' + esc(kv[0]) + '</td><td>' + esc(kv[1]) + '</td></tr>');
      });
      h.push('</table><h3>管理理念</h3><table class="tbl">');
      (K.culture.manage || []).forEach(function (kv) {
        h.push('<tr><td style="white-space:nowrap">' + esc(kv[0]) + '</td><td>' + esc(kv[1]) + '</td></tr>');
      });
      h.push('</table><div class="hint">' + esc(K.culture.note || '') + '</div></details>');

      if (K.cultureOld) {
        var co = K.cultureOld;
        h.push('<details class="acc"><summary>📁 2025 年前《企业文化手册》完整体系（旧题依据，需对照记忆）</summary>');
        h.push('<div class="hint">来源：' + esc(co.source) + '。' + esc(co.note) + '</div>');
        h.push('<table class="tbl">');
        (co.system || []).forEach(function (kv) {
          h.push('<tr><td style="white-space:nowrap">' + esc(kv[0]) + '</td><td>' + esc(kv[1]) + '</td></tr>');
        });
        h.push('</table>');
        if ((co.strategyDetail || []).length) {
          h.push('<h3>战略与方针条目释义</h3><table class="tbl">');
          co.strategyDetail.forEach(function (kv) {
            h.push('<tr><td style="white-space:nowrap">' + esc(kv[0]) + '</td><td>' + esc(kv[1]) + '</td></tr>');
          });
          h.push('</table>');
        }
        if ((co.special || []).length) {
          h.push('<h3>专项文化（旧版）</h3><table class="tbl">');
          co.special.forEach(function (kv) {
            h.push('<tr><td style="white-space:nowrap">' + esc(kv[0]) + '</td><td>' + esc(kv[1]) + '</td></tr>');
          });
          h.push('</table>');
        }
        h.push('<div class="feedback warn">' + esc(co.brandSloganNote || '') + '</div>');
        h.push('</details>');
      }

      h.push('<details class="acc"><summary>⚠️ 旧信息 → 已核实更新（' + (K.corrections || []).length + ' 项）</summary>');
      h.push('<div class="hint">本地资料多为 2022—2025 年版本，以下条目已按官网核实更新。旧值保留仅供对照。</div>');
      (K.corrections || []).forEach(function (x, i) {
        h.push('<details class="acc"><summary>' + (i + 1) + '. ' + esc(x.item) + '（' + esc(x.severity || '') + '）</summary>' +
          '<div class="feedback bad" style="margin-top:6px">旧：' + esc(x.old) + '<div class="hint">出处：' + esc(x.oldFrom || '—') + '</div></div>' +
          '<div class="feedback ok">现行：' + esc(x.now) + '<div class="hint">出处：' + esc(x.nowFrom || '—') + '</div></div>' +
          '</details>');
      });
      h.push('</details>');

      h.push('<details class="acc"><summary>企业文化速记卡片（' + (K.flashcards || []).length + ' 条，问→答）</summary>');
      (K.flashcards || []).forEach(function (f, i) {
        h.push('<details class="acc"><summary>Q' + (i + 1) + '. ' + esc(f.q) + '</summary><div>' + esc(f.a) + '</div></details>');
      });
      h.push('</details>');
    }
    h.push('</div>');

    h.push('<div class="card"><h2>业务板块速记</h2>');
    if (K.business) {
      Object.keys(K.business).forEach(function (k) {
        var label = { coal: '煤炭', power: '电力', chemical: '化工', transport: '运输', tech: '科技创新' }[k] || k;
        h.push('<details class="acc"><summary>' + esc(label) + '（' + K.business[k].length + ' 条）</summary><ul class="tight">');
        K.business[k].forEach(function (x) { h.push('<li>' + esc(x) + '</li>'); });
        h.push('</ul></details>');
      });
    }
    h.push('</div>');

    if (K.groupNews2026) {
      var gn = K.groupNews2026;
      h.push('<div class="card"><h2>集团近期要闻（2026 下半年，官网核实）</h2>');
      h.push('<div class="hint">' + esc(gn.note) + '　来源：' + esc(gn.source) + '</div>');
      h.push('<div class="scrollx"><table class="tbl"><tr><th>日期</th><th>板块</th><th>要闻与关键数据</th></tr>');
      (gn.items || []).forEach(function (x) {
        h.push('<tr><td style="white-space:nowrap">' + esc(x.date) + '</td><td>' + esc(x.cat) + '</td>' +
          '<td><strong>' + esc(x.title) + '</strong><br>' + esc(x.fact) + '</td></tr>');
      });
      h.push('</table></div>');
      if (gn.brandPositioning) h.push('<div class="hint">' + esc(gn.brandPositioning) + '</div>');
      if (gn.threePioneers) h.push('<div class="hint">' + esc(gn.threePioneers) + '</div>');
      h.push('</div>');
    }

    if (K.currentAffairs2026H2) {
      var h2 = K.currentAffairs2026H2;
      h.push('<div class="card"><h2>时政补充：' + esc(h2.coverage) + '（联网抓取）</h2>');
      h.push('<div class="feedback warn">本地资料止于 2026 年 4 月。<strong>尚未覆盖：' + esc(h2.uncovered) +
        '</strong>。' + esc(h2.note) + '</div>');
      h.push('<div class="scrollx"><table class="tbl"><tr><th>日期</th><th>类别</th><th>条目</th></tr>');
      (h2.items || []).forEach(function (x) {
        h.push('<tr><td style="white-space:nowrap">' + esc(x.date) + '</td><td>' + esc(x.cat) + '</td>' +
          '<td><strong>' + esc(x.title) + '</strong><br>' + esc(x.fact) +
          '<br><a href="' + esc(x.url) + '" target="_blank" rel="noopener">来源</a></td></tr>');
      });
      h.push('</table></div></div>');
    }

    var ca = K.currentAffairs;
    if (ca) {
      h.push('<div class="card"><h2>时政考点（' + esc(ca.coverage) + '）</h2>');
      h.push('<div class="feedback warn">资料覆盖：' + esc(ca.coverage) + '；<strong>缺失：' + esc(ca.missing) +
        '</strong>。' + esc(ca.sourceNote || '') + '</div>');
      h.push('<h3>国家能源集团直接命中考点</h3>');
      (ca.groupHits || []).forEach(function (x, i) {
        h.push('<details class="acc"><summary>' + (i + 1) + '. ' + esc(x.item) + '</summary>' +
          '<div>' + esc(x.fact) + '</div><div class="hint">出处：' + esc(x.src || '—') + '</div></details>');
      });
      if ((ca.numberTraps || []).length) {
        h.push('<h3>易混数字辨析</h3><ul class="tight">');
        ca.numberTraps.forEach(function (t) { h.push('<li>' + esc(t) + '</li>'); });
        h.push('</ul>');
      }
      h.push('<h3>问→答速记（' + (ca.flashcards || []).length + ' 条）</h3>');
      (ca.flashcards || []).forEach(function (f, i) {
        h.push('<details class="acc"><summary>Q' + (i + 1) + '. ' + esc(f.q) + '</summary><div>' + esc(f.a) + '</div></details>');
      });
      h.push('</div>');
    }

    h.push('<div class="card"><h2>备考报告（docs 目录）</h2>');
    h.push('<div class="hint">以下报告为本次资料整理与联网核实的成果，可直接点击查看（以 http 方式打开时）。</div>');
    h.push('<ul class="tight">');
    [
      ['docs/01_资料归纳总结.md', '资料归纳总结', '全量资料盘点、提取成果、题库构成与校验结果'],
      ['docs/02_老旧信息联网核实报告.md', '老旧信息联网核实报告', '过时信息逐条对照与官网核实结果'],
      ['docs/03_时政考点归纳.md', '时政考点归纳', '2026 年 1—4 月核心考点与问→答 65 条'],
      ['docs/04_行测EPI考点归纳.md', '行测 / EPI 考点归纳', '五大题型方法、原文例题与提分优先级'],
      ['docs/05_面试与专业知识归纳.md', '面试与专业知识归纳', '面试形式、专业知识范围与要点'],
      ['docs/06_题库校验报告.md', '题库校验报告', '全部异常条目明细'],
      ['docs/07_资料阅读覆盖度审计.md', '资料阅读覆盖度审计', '356 份资料逐份判定：哪些读了、哪些没读、为什么'],
      ['docs/08_政治理论考点归纳.md', '政治理论考点归纳', '十个明确、六个必须坚持、二十届三中全会、教育/民生/生态/外交/党建'],
      ['docs/09_历年真题与考情分析.md', '历年真题与考情分析', '真题/模拟题逐年题量、来源与领域分布（关键词命中，非官方分类）'],
      ['README.md', '使用说明（README）', '打开方式、功能、备份恢复、导入格式、已知限制'],
    ].forEach(function (d) {
      h.push('<li><a href="' + esc(d[0]) + '" target="_blank" rel="noopener">' + esc(d[1]) + '</a> —— ' + esc(d[2]) + '</li>');
    });
    h.push('</ul></div>');

    h.push('<div class="card"><h2>使用说明</h2><ul class="tight">' +
      '<li>建议用自带的 <code>start.cmd</code> 以 http 方式打开，可获得完整存储容量与 PWA 离线安装能力；直接双击 index.html 也可使用（存储会自动降级）。</li>' +
      '<li>答题记录保存在本机浏览器中。请定期使用“导出完整备份”，避免浏览器数据被清理后丢失。</li>' +
      '<li>题目与答案均标注来源文件；标为“待核对”的题目不计入正确率统计。</li>' +
      '<li>解析缺失时显示“原资料未提供解析”，APP 不会自动编写解析。</li>' +
      '</ul><div class="row" style="margin-top:10px">' +
      '<button class="btn-sm" data-act="wipe">清空全部学习数据（题库不受影响）</button></div></div>');
    return h.join('');
  }

  window.UI = {
    esc: esc, pct: pct, badge: badge, bar: bar,
    viewHome: viewHome, viewBank: viewBank, viewQuestion: viewQuestion,
    viewPractice: viewPractice, viewWrong: viewWrong, viewExam: viewExam,
    viewStats: viewStats, viewMore: viewMore,
    bankFilter: bankFilter, wrongFilter: wrongFilter, examSetup: examSetup,
    practiceStart: practiceStart, startPractice: startPractice, buildPool: buildPool,
    modeLabel: modeLabel,
  };
})();

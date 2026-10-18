/* 数据层：导出备份、恢复导入、题库导入（JSON/CSV）、校验报告生成。 */
(function () {
  'use strict';

  var IO = {
    download: function (filename, text, mime) {
      var blob = new Blob([text], { type: (mime || 'application/json') + ';charset=utf-8' });
      var url = URL.createObjectURL(blob);
      var a = document.createElement('a');
      a.href = url; a.download = filename;
      document.body.appendChild(a);
      a.click();
      setTimeout(function () { URL.revokeObjectURL(url); a.remove(); }, 800);
    },

    stamp: function () {
      var d = new Date();
      function p(n) { return n < 10 ? '0' + n : '' + n; }
      return d.getFullYear() + p(d.getMonth() + 1) + p(d.getDate()) + '-' + p(d.getHours()) + p(d.getMinutes());
    },

    /* ------------------------------------------------------------ 导出 */
    exportProgress: function (state) {
      IO.download('国能备考-学习记录-' + IO.stamp() + '.json', JSON.stringify({
        kind: 'ce-study-progress', version: 1, exportedAt: new Date().toISOString(),
        progress: state.progress, wrongBook: state.wrongBook, logs: state.logs,
        exams: state.exams, meta: state.meta,
      }, null, 1));
    },

    exportBank: function (state) {
      var imported = Bank.custom || [];
      IO.download('国能备考-题库-' + IO.stamp() + '.json', JSON.stringify({
        kind: 'ce-question-bank', schemaVersion: 1,
        exportedAt: new Date().toISOString(),
        count: Bank.all.length,
        custom: imported,
      }, null, 1));
    },

    exportBackup: function (state) {
      IO.download('国能备考-完整备份-' + IO.stamp() + '.json', JSON.stringify({
        kind: 'ce-full-backup', version: 1, exportedAt: new Date().toISOString(),
        meta: state.meta, progress: state.progress, wrongBook: state.wrongBook,
        logs: state.logs, exams: state.exams, sessions: state.sessions,
        customBank: { schemaVersion: 1, questions: Bank.custom || [] },
      }, null, 1));
    },

    exportValidation: function (report, bankInfo) {
      var L = [];
      L.push('# 题库校验报告');
      L.push('');
      L.push('- 生成时间：' + new Date().toLocaleString('zh-CN'));
      L.push('- 题库总量：' + report.total + ' 题');
      if (bankInfo) {
        L.push('- 内置题目：' + bankInfo.builtin + ' 题；导入题目：' + bankInfo.imported + ' 题');
        L.push('- 题库生成日期：' + (bankInfo.generatedAt || '未知'));
      }
      L.push('- 重复 ID：' + report.duplicateIds.length + ' 个');
      L.push('- 异常条目：' + report.issueCount + ' 条');
      L.push('');
      L.push('## 异常类型统计');
      Object.keys(report.byIssue).sort(function (a, b) { return report.byIssue[b] - report.byIssue[a]; })
        .forEach(function (k) { L.push('- ' + k + '：' + report.byIssue[k]); });
      L.push('');
      L.push('## 异常明细（最多 500 条）');
      report.issues.slice(0, 500).forEach(function (it) {
        L.push('- `' + it.id + '` ' + it.kind + '｜题干：' + (it.stem || '').replace(/\n/g, ' ') + '｜来源：' + (it.source || ''));
      });
      L.push('');
      L.push('## 说明');
      L.push('- “解析缺失”不是错误：原资料未提供解析时如实标注，APP 不会自动编写解析。');
      L.push('- “答案待核对”的题目不纳入正确率统计，也不会被当作已验证答案使用。');
      IO.download('国能备考-题库校验报告-' + IO.stamp() + '.md', L.join('\n'), 'text/markdown');
      return L.join('\n');
    },

    /* ------------------------------------------------------------ 模板 */
    csvTemplate: function () {
      var head = 'id,type,stem,optionA,optionB,optionC,optionD,answer,explanation,category,chapter,tags,sourceFile';
      var sample = [
        '# 说明：type 取 single_choice / multiple_choice / true_false / fill_blank / short_answer',
        '# 多选答案用竖线分隔，如 A|C ；判断题 answer 填 正确 或 错误',
        '# 填空题 answer 可写多个可接受答案，用竖线分隔',
        '# 以 # 开头的行会被忽略；请勿删除表头行',
      ].join('\n');
      var row = 'demo-1,single_choice,示例题干（请替换）,选项甲,选项乙,选项丙,选项丁,A,示例解析（可留空）,自定义,示例章节,标签1|标签2,自编题目.csv';
      IO.download('国能备考-题库导入模板.csv', '\ufeff' + sample + '\n' + head + '\n' + row + '\n', 'text/csv');
    },

    /* ------------------------------------------------------------ 解析 */
    parseJSON: function (text) {
      var data = JSON.parse(text);
      var qs = null;
      if (Array.isArray(data)) qs = data;
      else if (data && Array.isArray(data.questions)) qs = data.questions;
      else if (data && Array.isArray(data.custom)) qs = data.custom;
      if (!qs) throw new Error('未找到题目数组（应为 {questions:[...]} 或 [...]）');
      return {
        kind: (data && data.kind) || 'ce-question-bank',
        questions: qs,
        raw: data,
      };
    },

    parseCSV: function (text) {
      text = text.replace(/^\ufeff/, '');
      var lines = text.split(/\r?\n/).filter(function (l) {
        return l.trim() && l.trim().charAt(0) !== '#';
      });
      if (!lines.length) throw new Error('CSV 为空');
      var head = splitCSVLine(lines[0]);
      var idx = {};
      head.forEach(function (h, i) { idx[h.trim()] = i; });
      if (idx.stem === undefined) throw new Error('CSV 缺少 stem 列');
      var out = [];
      for (var i = 1; i < lines.length; i++) {
        var cells = splitCSVLine(lines[i]);
        function g(name) {
          var k = idx[name];
          return k === undefined ? '' : (cells[k] || '').trim();
        }
        var opts = [];
        ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'].forEach(function (L) {
          var v = g('option' + L);
          if (v) opts.push({ key: L, text: v });
        });
        var ansRaw = g('answer');
        var answers = ansRaw.indexOf('|') >= 0
          ? ansRaw.split('|').map(function (s) { return s.trim(); }).filter(Boolean)
          : (ansRaw ? [ansRaw.trim()] : []);
        out.push({
          type: g('type') || (opts.length ? 'single_choice' : 'fill_blank'),
          stem: g('stem'),
          options: opts,
          answer: answers,
          explanation: g('explanation'),
          category: g('category') || '自定义',
          chapter: g('chapter') || '自定义导入',
          tags: g('tags') ? g('tags').split('|').map(function (s) { return s.trim(); }) : [],
          sourceFile: g('sourceFile') || '用户导入 CSV',
          id: g('id') || '',
        });
      }
      return { kind: 'ce-question-bank', questions: out, raw: out };
    },

    /* --------------------------------------------------- 导入校验与预览 */
    validateImport: function (questions) {
      var issues = [];
      var ok = 0;
      var ids = {};
      questions.forEach(function (q, i) {
        var label = '第 ' + (i + 1) + ' 条';
        if (!q.stem || !String(q.stem).trim()) issues.push(label + '：题干为空');
        var t = q.type || 'single_choice';
        if (['single_choice', 'multiple_choice', 'true_false', 'fill_blank', 'short_answer'].indexOf(t) < 0) {
          issues.push(label + '：未知题型 ' + t);
        }
        var ans = q.answer || [];
        if (!Array.isArray(ans)) ans = [ans];
        if (!ans.length) issues.push(label + '：答案缺失');
        if (t === 'single_choice' || t === 'multiple_choice') {
          var opts = q.options || [];
          if (opts.length < 2) issues.push(label + '：选项不足 2 个');
          var keys = opts.map(function (o) { return String(o.key).toUpperCase(); });
          ans.forEach(function (a) {
            if (keys.indexOf(String(a).toUpperCase()) < 0) issues.push(label + '：答案 ' + a + ' 不在选项中');
          });
        }
        if (q.id && ids[q.id]) issues.push(label + '：ID 重复 ' + q.id);
        if (q.id) ids[q.id] = 1;
        if (!issues.length || issues[issues.length - 1].indexOf(label) < 0) ok++;
      });
      return { count: questions.length, ok: questions.length - countIssueLabels(issues), issues: issues };
    },

    /** 应用导入的题库（导入的题目单独存放，不与内置题库混写） */
    applyBank: function (questions, mode) {
      var norm = questions.map(function (q, i) {
        var ans = q.answer || [];
        if (!Array.isArray(ans)) ans = [ans];
        return {
          id: q.id || ('imported-' + Date.now() + '-' + i),
          type: q.type || (q.options && q.options.length ? 'single_choice' : 'fill_blank'),
          stem: String(q.stem || '').trim(),
          options: (q.options || []).map(function (o) {
            return { key: String(o.key || '').toUpperCase(), text: String(o.text || '') };
          }),
          answer: ans.map(function (a) { return String(a); }),
          explanation: q.explanation || '',
          answerStatus: ans.length ? 'verified' : 'missing',
          category: q.category || '自定义',
          chapter: q.chapter || '自定义导入',
          knowledgePoints: q.knowledgePoints || [],
          difficulty: q.difficulty || 'medium',
          tags: q.tags || [],
          passageId: null, assets: [], enabled: true,
          sourceFile: q.sourceFile || '用户导入',
          sourcePage: q.sourcePage || null,
        };
      }).filter(function (q) { return q.stem; });

      var existing = (mode === 'append') ? (Bank.custom || []).slice() : [];
      var seen = {};
      existing.forEach(function (q) { seen[Bank.normStem(q.stem) + '|' + (q.answer || []).join('')] = 1; });
      var added = 0, skipped = 0;
      norm.forEach(function (q) {
        var k = Bank.normStem(q.stem) + '|' + (q.answer || []).join('');
        if (seen[k]) { skipped++; return; }
        seen[k] = 1;
        existing.push(q);
        added++;
      });
      return Store.set('customBank', {
        schemaVersion: 1, importedAt: new Date().toISOString(),
        questions: existing,
      }).then(function () {
        return { added: added, skipped: skipped, total: existing.length };
      });
    },

    /** 恢复学习记录（合并或替换） */
    applyProgress: function (payload, mode) {
      return Promise.all([Store.get('progress', {}), Store.get('wrongBook', {}),
        Store.get('logs', {}), Store.get('exams', []), Store.get('meta', null)])
        .then(function (cur) {
          var p = cur[0] || {}, wb = cur[1] || {}, logs = cur[2] || {}, exams = cur[3] || [], meta = cur[4] || {};
          if (mode === 'replace') {
            p = payload.progress || {}; wb = payload.wrongBook || {};
            logs = payload.logs || {}; exams = payload.exams || [];
          } else {
            Object.keys(payload.progress || {}).forEach(function (id) {
              var a = p[id], b = payload.progress[id];
              if (!a) { p[id] = b; return; }
              a.seen = (a.seen || 0) + (b.seen || 0);
              a.correctCount = (a.correctCount || 0) + (b.correctCount || 0);
              a.wrongCount = (a.wrongCount || 0) + (b.wrongCount || 0);
              a.fav = !!(a.fav || b.fav);
              if ((b.lastAt || 0) > (a.lastAt || 0)) {
                a.lastAt = b.lastAt; a.mastery = b.mastery || a.mastery;
                a.reviewDue = b.reviewDue || a.reviewDue;
                a.wrongReason = b.wrongReason || a.wrongReason;
              }
            });
            Object.keys(payload.wrongBook || {}).forEach(function (id) {
              wb[id] = (wb[id] || 0) + payload.wrongBook[id];
            });
            Object.keys(payload.logs || {}).forEach(function (d) {
              if (!logs[d]) { logs[d] = payload.logs[d]; return; }
              logs[d].answered += payload.logs[d].answered || 0;
              logs[d].correct += payload.logs[d].correct || 0;
              logs[d].wrong += payload.logs[d].wrong || 0;
              logs[d].minutes += payload.logs[d].minutes || 0;
            });
            (payload.exams || []).forEach(function (e) {
              if (!exams.some(function (x) { return x.id === e.id; })) exams.push(e);
            });
          }
          if (payload.meta && payload.meta.targetDate && !meta.targetDate) meta.targetDate = payload.meta.targetDate;
          return Promise.all([
            Store.set('progress', p), Store.set('wrongBook', wb), Store.set('logs', logs),
            Store.set('exams', exams), Store.set('meta', meta),
          ]).then(function () {
            return { progress: Object.keys(p).length, wrong: Object.keys(wb).length, exams: exams.length };
          });
        });
    },
  };

  function splitCSVLine(line) {
    var out = [], cur = '', inQ = false;
    for (var i = 0; i < line.length; i++) {
      var c = line[i];
      if (inQ) {
        if (c === '"') {
          if (line[i + 1] === '"') { cur += '"'; i++; }
          else inQ = false;
        } else cur += c;
      } else if (c === '"') inQ = true;
      else if (c === ',') { out.push(cur); cur = ''; }
      else cur += c;
    }
    out.push(cur);
    return out;
  }

  function countIssueLabels(issues) {
    var labels = {};
    issues.forEach(function (s) { var m = /^第 (\d+) 条/.exec(s); if (m) labels[m[1]] = 1; });
    return Object.keys(labels).length;
  }

  window.IO = IO;
})();

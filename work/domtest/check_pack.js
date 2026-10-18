'use strict';
const fs = require('fs'), path = require('path');
const { JSDOM } = require('jsdom');
const APP = 'D:\\DOWNLOADS\\app';
const dom = new JSDOM(fs.readFileSync(path.join(APP,'index.html'),'utf8'),
  { runScripts:'outside-only', pretendToBeVisual:true, url:'http://127.0.0.1:8777/index.html' });
const w = dom.window;
w.scrollTo=()=>{}; w.confirm=()=>true; w.alert=()=>{}; w.console.log=()=>{};
w.HTMLElement.prototype.scrollIntoView=()=>{};
if (!w.URL.createObjectURL) w.URL.createObjectURL=()=>'blob:stub';
for (const rel of ['data/questions.js','data/knowledge.js','js/store.js','js/bank.js',
  'js/practice.js','js/exam.js','js/stats.js','js/io.js','js/ui.js','js/app.js'])
  w.eval(fs.readFileSync(path.join(APP, rel),'utf8'));
const csv = fs.readFileSync(path.join(APP,'可选导入','专业知识练习题_计算机类.csv'),'utf8');
const parsed = w.IO.parseCSV(csv);
console.log('APP parseCSV 解析题数:', parsed.questions.length);
const q0 = parsed.questions[0];
console.log('首题字段:', JSON.stringify({id:q0.id,type:q0.type,stem:(q0.stem||'').slice(0,40),
  opts:(q0.options||[]).length, answer:q0.answer, category:q0.category}).slice(0,200));
const bad = parsed.questions.filter(q => !q.stem || !(q.options||[]).length || !(q.answer||[]).length);
console.log('缺题干/选项/答案的条目:', bad.length);
process.exit(0);

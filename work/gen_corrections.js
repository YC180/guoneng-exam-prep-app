/* 生成《老旧信息联网核实报告》—— 直接取自 app/data/knowledge.js，保证与 APP 内一致。 */
'use strict';
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const APP = 'D:\\DOWNLOADS\\app';
const OUT = path.join(APP, 'docs', '02_老旧信息联网核实报告.md');

const sandbox = { console, Date, Math, JSON, Object, Array, String, Number, Boolean, RegExp, parseInt, parseFloat };
sandbox.window = sandbox;
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync(path.join(APP, 'data', 'knowledge.js'), 'utf8'), sandbox, { filename: 'knowledge.js' });
const K = sandbox.window.CE_KNOWLEDGE;

const L = [];
const A = (s) => L.push(s);

A('# 老旧信息联网核实报告');
A('');
A('国家能源集团备考资料 —— 过时信息逐条核实与更新');
A('');
A(`- 核实日期：**${K.verifiedAt}**`);
A(`- 核实方式：逐页抓取官方网站原文比对（搜索工具不可用，均按已知官方网址直接抓取）`);
A('- 比对基准：`ceic.com` 官网集团概况页、企业文化页、集团领导页');
A('- 处理原则：**凡与官网冲突处以官网为准**；旧值全部保留，供识别旧题答案之用');
A('');

A('## 一、核实来源');
A('');
A('| 来源 | 网址 |');
A('|---|---|');
(K.sources || []).forEach((s) => A(`| ${s.name} | ${s.url} |`));
A('');
A('> 说明：本次会话中关键词搜索接口不可用（HTTP 402），因此**无法穷尽检索**所有可能过时的表述。');
A('> 已核实项均为可直接访问的官方页面原文；未能核实的项目已如实列入第六节“待核清单”。');
A('');

A('## 二、集团概况（2026 官方口径）');
A('');
const c = K.company || {};
A('| 项目 | 现行表述 |');
A('|---|---|');
[['全称', c.fullName], ['简称 / 英文简称', `${c.shortName || ''} / ${c.enShort || ''}`],
 ['挂牌成立', c.founded], ['重组来源', c.origin], ['世界500强', c.fortune500],
 ['总资产', c.assets], ['员工人数', c.staff], ['定位', c.positioning],
 ['煤炭产能', c.coalCapacity], ['发电装机', c.powerCapacity], ['铁路', c.railway],
 ['港口吞吐', c.port], ['化工品产能', c.chemical], ['上市公司', c.listed],
 ['业务布局', c.coverage], ['经营业绩考核', c.award]].forEach(([k, v]) => {
  if (v) A(`| ${k} | ${v} |`);
});
A('');
if ((c.shares || []).length) {
  A('**占全国比重**：' + c.shares.map((s) => `${s[0]}${s[1]}`).join('；') + '。');
  A('');
}

A('## 三、集团领导（官网 2026-10-18）');
A('');
A('| 姓名 | 职务 |');
A('|---|---|');
((K.leaders || {}).list || []).forEach((l) => A(`| ${l[0]} | ${l[1]} |`));
A('');
A('> ⚠️ **最高优先级更正**：本地《企业文化试题》第 21 题与《三色笔记》等资料写作**刘国跃**任党组书记、董事长，');
A('> 官网现任为**邹磊**。此为必考人名，务必更新。');
A('');

A('## 四、企业文化核心理念（2025 官网新版）');
A('');
A(K.culture ? K.culture.note : '');
A('');
A('### 核心条目');
A('');
A('| 条目 | 表述 |');
A('|---|---|');
((K.culture || {}).core || []).forEach((kv) => A(`| ${kv[0]} | ${kv[1]} |`));
A('');
A('### 发展理念');
A('');
A('| 条目 | 表述 |');
A('|---|---|');
((K.culture || {}).develop || []).forEach((kv) => A(`| ${kv[0]} | ${kv[1]} |`));
A('');
A('### 管理理念（九条）');
A('');
A('| 条目 | 表述 |');
A('|---|---|');
((K.culture || {}).manage || []).forEach((kv) => A(`| ${kv[0]} | ${kv[1]} |`));
A('');
A('### 精神谱系');
A('');
A('| 条目 | 表述 |');
A('|---|---|');
((K.culture || {}).heritage || []).forEach((kv) => A(`| ${kv[0]} | ${kv[1]} |`));
A('');

if (K.cultureOld) {
  A('## 五、2025 年前版《企业文化手册》完整体系（旧题依据）');
  A('');
  A(`- 来源：${K.cultureOld.source}`);
  A(`- ${K.cultureOld.note}`);
  A('');
  A('| 条目 | 2025 年前表述 |');
  A('|---|---|');
  (K.cultureOld.system || []).forEach((kv) => A(`| ${kv[0]} | ${kv[1]} |`));
  A('');
  A('### 战略与方针条目释义');
  A('');
  A('| 条目 | 释义 |');
  A('|---|---|');
  (K.cultureOld.strategyDetail || []).forEach((kv) => A(`| ${kv[0]} | ${kv[1]} |`));
  A('');
  A('### 专项文化（旧版）');
  A('');
  A('| 条目 | 表述 |');
  A('|---|---|');
  (K.cultureOld.special || []).forEach((kv) => A(`| ${kv[0]} | ${kv[1]} |`));
  A('');
  if (K.cultureOld.brandSloganNote) {
    A(`> ${K.cultureOld.brandSloganNote}`);
    A('');
  }
}

A('## 六、过时信息逐条对照表');
A('');
A(`共 **${(K.corrections || []).length}** 项。`);
A('');
A('| # | 项目 | 旧表述（资料） | 旧值出处 | 现行表述（官网核实） | 核实来源 | 严重度 |');
A('|---:|---|---|---|---|---|---|');
(K.corrections || []).forEach((x, i) => {
  const cl = (s) => String(s == null ? '' : s).replace(/\|/g, '\\|').replace(/\n/g, ' ');
  A(`| ${i + 1} | ${cl(x.item)} | ${cl(x.old)} | ${cl(x.oldFrom)} | ${cl(x.now)} | ${cl(x.nowFrom)} | ${cl(x.severity)} |`);
});
A('');

A('## 七、待核清单（无法通过公开页面确认的项目）');
A('');
A('以下项目**未能取得官方文字**，APP 中一律标注存疑，不作确定性表述：');
A('');
A('1. **品牌口号** —— 2025 官网与 2025 年前版手册均以**图像**发布该条目，无法取得文字。旧资料写作“国家能源——不断前进的动力”，未获官方确认。');
A('2. **题型/题量/分值分布** —— 本地讲义仅载“行测一般时间为 60—80 分钟不等”“一个单项选择题对应时间约 1 分钟”，未提供总分与各模块题量。');
A('3. **实际笔试日期与公告** —— 本地资料无 2026 年招聘公告原文；APP 中的 2026-10-24 为**用户设定的学习完成目标日**，非笔试日期。');
A('4. **2026 年 5—10 月时政** —— 原资料目录明确“已更 4 月”。已联网补充 2026 年 7—10 月部分条目（见下节），');
A('   **5 月、6 月、8 月仍未覆盖**；且抓取到的是公开报道条目，不等同于机构的应试提炼。');
A('5. **部分题目答案** —— 见题库校验报告中的“待核对”“无答案”条目，均不猜测。');
A('');

if (K.currentAffairs2026H2) {
  const h2 = K.currentAffairs2026H2;
  A('## 八、2026 年下半年时政补充（联网抓取）');
  A('');
  A(`- 覆盖：${h2.coverage}`);
  A(`- 未覆盖：${h2.uncovered}`);
  A(`- ${h2.note}`);
  A('');
  A('| 日期 | 类别 | 条目 | 来源 |');
  A('|---|---|---|---|');
  (h2.items || []).forEach((x) => {
    const cl = (s) => String(s == null ? '' : s).replace(/\|/g, '\\|').replace(/\n/g, ' ');
    A(`| ${x.date} | ${x.cat} | **${cl(x.title)}** ${cl(x.fact)} | ${x.url} |`);
  });
  A('');
}

A('## 九、集团近期要闻（2026 下半年，官网核实）');
A('');
if (K.groupNews2026) {
  A(`- 来源：${K.groupNews2026.source}`);
  A(`- ${K.groupNews2026.note}`);
  A('');
  A('| 日期 | 板块 | 要闻 | 关键事实 |');
  A('|---|---|---|---|');
  (K.groupNews2026.items || []).forEach((x) => {
    A(`| ${x.date} | ${x.cat} | ${x.title} | ${x.fact} |`);
  });
  A('');
  if (K.groupNews2026.brandPositioning) A(`> ${K.groupNews2026.brandPositioning}`);
  if (K.groupNews2026.threePioneers) A(`> ${K.groupNews2026.threePioneers}`);
  A('');
}

A('## 十、修订记录');
A('');
A(`- ${K.verifiedAt}：完成官网核对，新增/更新 ${(K.corrections || []).length} 项过时信息对照。`);
A('- 同日：从《国家能源企业文化核心理念.pdf》（62 页，含文字层）提取 2025 年前版完整体系，用于新旧对照。');
A('- 同日：核实来源 4 个官方页面（集团概况、企业文化、集团领导、业务体系）。');
A('');

A('---');
A('');
A('> 本报告的机器可读版本即 `app/data/knowledge.js`，APP 内「资料与设置 → 已核实知识点」展示同一份数据，');
A('> 二者始终一致。');
A('');

fs.mkdirSync(path.dirname(OUT), { recursive: true });
fs.writeFileSync(OUT, L.join('\n'), 'utf8');
console.log(`写出 ${OUT}（${L.length} 行）`);
console.log(`corrections: ${(K.corrections || []).length} 项，leaders: ${((K.leaders || {}).list || []).length} 人，flashcards: ${(K.flashcards || []).length} 条，时政速记: ${((K.currentAffairs || {}).flashcards || []).length} 条`);

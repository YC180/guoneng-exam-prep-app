/* Service Worker：应用外壳离线缓存。
 * 仅在以 http(s) 打开时生效；file:// 下浏览器不会注册 SW（页面本身已可离线使用）。
 */
var CACHE = 'ce-study-v5';   /* 题库/文档更新后递增，强制刷新离线缓存 */
var ASSETS = [
  './',
  './index.html',
  './manifest.webmanifest',
  './css/app.css',
  './data/questions.js',
  './data/knowledge.js',
  './js/store.js',
  './js/bank.js',
  './js/practice.js',
  './js/exam.js',
  './js/stats.js',
  './js/io.js',
  './js/ui.js',
  './js/app.js',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/icon.svg',
  './README.md',
  /* 8 份整理报告也要预缓存：APP 内「资料与设置」可离线打开它们，
     否则在 http 模式下断网后这些报告会加载失败。 */
  './docs/01_资料归纳总结.md',
  './docs/02_老旧信息联网核实报告.md',
  './docs/03_时政考点归纳.md',
  './docs/04_行测EPI考点归纳.md',
  './docs/05_面试与专业知识归纳.md',
  './docs/06_题库校验报告.md',
  './docs/07_资料阅读覆盖度审计.md',
  './docs/08_政治理论考点归纳.md',
  './docs/09_历年真题与考情分析.md',
];

self.addEventListener('install', function (ev) {
  ev.waitUntil(
    caches.open(CACHE).then(function (c) {
      /* 逐个添加：单个失败不影响整体安装 */
      return Promise.all(ASSETS.map(function (u) {
        return c.add(new Request(u, { cache: 'reload' })).catch(function () { return null; });
      }));
    }).then(function () { return self.skipWaiting(); })
  );
});

self.addEventListener('activate', function (ev) {
  ev.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(keys.map(function (k) {
        return k === CACHE ? null : caches.delete(k);
      }));
    }).then(function () { return self.clients.claim(); })
  );
});

self.addEventListener('fetch', function (ev) {
  var req = ev.request;
  if (req.method !== 'GET') return;
  var url = new URL(req.url);
  if (url.origin !== location.origin) return;

  /* 数据与外壳：缓存优先，网络回退并更新 */
  ev.respondWith(
    caches.match(req).then(function (hit) {
      if (hit) {
        fetch(req).then(function (res) {
          if (res && res.status === 200) caches.open(CACHE).then(function (c) { c.put(req, res); });
        }).catch(function () { /* 离线：忽略 */ });
        return hit;
      }
      return fetch(req).then(function (res) {
        if (res && res.status === 200 && res.type === 'basic') {
          var copy = res.clone();
          caches.open(CACHE).then(function (c) { c.put(req, copy); });
        }
        return res;
      }).catch(function () {
        if (req.mode === 'navigate') return caches.match('./index.html');
        return new Response('离线且未缓存', { status: 503, headers: { 'Content-Type': 'text/plain;charset=utf-8' } });
      });
    })
  );
});

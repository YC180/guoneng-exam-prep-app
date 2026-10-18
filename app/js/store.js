/* 持久化层：优先 IndexedDB，失败时回退 localStorage。
 * 注意：以 file:// 直接打开时，部分浏览器会限制 IndexedDB；
 * 此时自动回退到 localStorage，功能不受影响（容量较小）。
 * 建议使用自带的 start.cmd 以 http 方式打开，可获得完整容量与 PWA 安装能力。
 */
(function () {
  'use strict';

  var DB_NAME = 'ce_study_db';
  var DB_VER = 1;
  var STORE = 'kv';
  var LS_PREFIX = 'ce_study::';

  var backend = null;   // 'idb' | 'ls'
  var db = null;
  var mem = {};         // 极端情况下（两者都不可用）的内存回退

  function lsAvailable() {
    try {
      localStorage.setItem(LS_PREFIX + '__t', '1');
      localStorage.removeItem(LS_PREFIX + '__t');
      return true;
    } catch (e) { return false; }
  }

  function openIDB() {
    return new Promise(function (resolve, reject) {
      if (!window.indexedDB) return reject(new Error('no indexedDB'));
      var req;
      try { req = indexedDB.open(DB_NAME, DB_VER); }
      catch (e) { return reject(e); }
      var settled = false;
      var timer = setTimeout(function () {
        if (!settled) { settled = true; reject(new Error('indexedDB open timeout')); }
      }, 3000);
      req.onupgradeneeded = function () {
        var d = req.result;
        if (!d.objectStoreNames.contains(STORE)) d.createObjectStore(STORE);
      };
      req.onsuccess = function () {
        if (settled) return;
        settled = true; clearTimeout(timer);
        resolve(req.result);
      };
      req.onerror = function () {
        if (settled) return;
        settled = true; clearTimeout(timer);
        reject(req.error || new Error('indexedDB open error'));
      };
      req.onblocked = function () {
        if (settled) return;
        settled = true; clearTimeout(timer);
        reject(new Error('indexedDB blocked'));
      };
    });
  }

  function idbGet(key) {
    return new Promise(function (resolve, reject) {
      var tx = db.transaction(STORE, 'readonly');
      var r = tx.objectStore(STORE).get(key);
      r.onsuccess = function () { resolve(r.result === undefined ? null : r.result); };
      r.onerror = function () { reject(r.error); };
    });
  }

  function idbSet(key, val) {
    return new Promise(function (resolve, reject) {
      var tx = db.transaction(STORE, 'readwrite');
      var r = tx.objectStore(STORE).put(val, key);
      r.onsuccess = function () { resolve(true); };
      r.onerror = function () { reject(r.error); };
    });
  }

  function idbKeys() {
    return new Promise(function (resolve, reject) {
      var tx = db.transaction(STORE, 'readonly');
      var r = tx.objectStore(STORE).getAllKeys();
      r.onsuccess = function () { resolve(r.result || []); };
      r.onerror = function () { reject(r.error); };
    });
  }

  var Store = {
    backendName: function () { return backend; },

    init: function () {
      return openIDB().then(function (d) {
        db = d; backend = 'idb';
        return 'idb';
      }).catch(function () {
        backend = lsAvailable() ? 'ls' : 'mem';
        return backend;
      });
    },

    get: function (key, fallback) {
      if (backend === 'idb') {
        return idbGet(key).then(function (v) { return v === null ? (fallback === undefined ? null : fallback) : v; })
          .catch(function () { return fallback === undefined ? null : fallback; });
      }
      if (backend === 'ls') {
        try {
          var raw = localStorage.getItem(LS_PREFIX + key);
          return Promise.resolve(raw === null ? (fallback === undefined ? null : fallback) : JSON.parse(raw));
        } catch (e) { return Promise.resolve(fallback === undefined ? null : fallback); }
      }
      return Promise.resolve(key in mem ? mem[key] : (fallback === undefined ? null : fallback));
    },

    set: function (key, val) {
      if (backend === 'idb') {
        return idbSet(key, val).catch(function () {
          backend = lsAvailable() ? 'ls' : 'mem';
          return Store.set(key, val);
        });
      }
      if (backend === 'ls') {
        try { localStorage.setItem(LS_PREFIX + key, JSON.stringify(val)); return Promise.resolve(true); }
        catch (e) {
          backend = 'mem'; mem[key] = val;
          return Promise.resolve(false);
        }
      }
      mem[key] = val;
      return Promise.resolve(true);
    },

    keys: function () {
      if (backend === 'idb') return idbKeys().catch(function () { return []; });
      if (backend === 'ls') {
        var out = [];
        for (var i = 0; i < localStorage.length; i++) {
          var k = localStorage.key(i);
          if (k && k.indexOf(LS_PREFIX) === 0) out.push(k.slice(LS_PREFIX.length));
        }
        return Promise.resolve(out);
      }
      return Promise.resolve(Object.keys(mem));
    },

    /* 清空学习数据（保留题库文件本身） */
    clearAll: function () {
      if (backend === 'idb') {
        return new Promise(function (resolve) {
          var tx = db.transaction(STORE, 'readwrite');
          tx.objectStore(STORE).clear();
          tx.oncomplete = function () { resolve(true); };
          tx.onerror = function () { resolve(false); };
        });
      }
      if (backend === 'ls') {
        var ks = [];
        for (var i = 0; i < localStorage.length; i++) {
          var k = localStorage.key(i);
          if (k && k.indexOf(LS_PREFIX) === 0) ks.push(k);
        }
        ks.forEach(function (k) { localStorage.removeItem(k); });
        return Promise.resolve(true);
      }
      mem = {};
      return Promise.resolve(true);
    },
  };

  window.Store = Store;
})();

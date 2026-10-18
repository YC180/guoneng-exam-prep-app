#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""离线自足性校验：APP 是否完全自包含、Service Worker 预缓存是否覆盖全部资源。

检查四件事：
  1) 运行时文件里有没有**外部 http(s) 依赖**（SVG XML 命名空间不算网络请求）；
  2) sw.js 的 ASSETS 清单内路径是否都真实存在；
  3) 反向确认：磁盘上有哪些文件**没被预缓存**，并说明它们是否本就无需缓存；
  4) APP 内列出的 8 份报告是否都在磁盘上、且已预缓存。
"""
import os
import re
import sys

APP = r"D:\DOWNLOADS\app"
# 无需预缓存的：sw 自身、命令行启动脚本（仅双击启动用，页面不加载）
NO_CACHE_OK = {"sw.js", "start.cmd", "start.ps1"}


def main():
    os.chdir(APP)
    sw = open("sw.js", encoding="utf-8").read()
    m = re.search(r"ASSETS\s*=\s*\[(.*?)\]", sw, re.S)
    listed = [x.lstrip("./") for x in re.findall(r"['\"]([^'\"]+)['\"]", m.group(1))] if m else []
    listed = [x for x in listed if x]
    cache = (re.search(r"CACHE\s*=\s*['\"]([^'\"]+)", sw) or [None, "?"])[1]

    print(f"sw.js 缓存版本: {cache}")
    print(f"预缓存条目: {len(listed)}")

    print("\n【1】外部依赖（只算“会被浏览器真去请求”的引用）")
    # 真正会产生网络请求的形态：script/link/iframe 的 src|href、CSS url()、
    # fetch/http 请求、import()、new Worker()。数据里的**来源 URL（引用出处）**
    # 只是文本/可点击链接，不加载任何资源，因此不算依赖。
    LOADERS = [
        re.compile(r"<script[^>]+src\s*=\s*['\"](https?:)?//", re.I),
        re.compile(r"<link[^>]+href\s*=\s*['\"](https?:)?//", re.I),
        re.compile(r"<iframe[^>]+src\s*=\s*['\"](https?:)?//", re.I),
        re.compile(r"<img[^>]+src\s*=\s*['\"](https?:)?//", re.I),
        re.compile(r"url\(\s*['\"]?(https?:)?//", re.I),
        re.compile(r"\bfetch\s*\(\s*['\"](https?:)?//", re.I),
        re.compile(r"\bimport\s*\(\s*['\"](https?:)?//", re.I),
        re.compile(r"new\s+Worker\s*\(\s*['\"](https?:)?//", re.I),
        re.compile(r"@import\s+['\"]?(https?:)?//", re.I),
    ]
    loaders, citations = [], 0
    for dp, _dn, fs in os.walk("."):
        for f in fs:
            if os.path.splitext(f)[1].lower() not in {".html", ".css", ".js", ".webmanifest"}:
                continue
            p = os.path.join(dp, f)
            for i, line in enumerate(open(p, encoding="utf-8", errors="replace"), 1):
                if any(rx.search(line) for rx in LOADERS):
                    loaders.append((p, i, line.strip()[:90]))
                citations += len(re.findall(r"https?://(?!www\.w3\.org)", line))
    if loaders:
        for p, i, l in loaders[:20]:
            print(f"  ⚠️ {p}:{i}  {l}")
    else:
        print("  ✅ 没有任何外部 script/link/iframe/fetch 引用 —— 完全自包含")
    print(f"  （另有 {citations} 处 http(s) 字样属**来源出处标注**，以文本/链接形式展示，")
    print("    不会发起请求，不影响离线使用。）")

    print("\n【2】预缓存清单内路径真实性")
    ghost = [x for x in listed if not os.path.exists(x)]
    print("  ✅ 全部存在" if not ghost else f"  ❌ 磁盘不存在：{ghost}")

    print("\n【3】未被预缓存的文件")
    actual = []
    for dp, _dn, fs in os.walk("."):
        for f in fs:
            actual.append(os.path.relpath(os.path.join(dp, f), ".").replace("\\", "/"))
    not_cached = sorted(a for a in actual if a not in listed)
    missing_rt = [a for a in not_cached
                  if a not in NO_CACHE_OK and not a.startswith("可选导入/")]
    for a in not_cached:
        if a in NO_CACHE_OK:
            tag = "（无需缓存：命令行启动脚本 / SW 自身）"
        elif a.startswith("可选导入/"):
            tag = "（无需缓存：可选导入包，需要时手动导入，不被页面加载）"
        else:
            tag = "❌ 运行时资源却未缓存"
        print(f"  {a}  {tag}")
    if not missing_rt:
        print("  ✅ 所有运行时资源均已预缓存，离线打开报告也不会失败")

    print("\n【4】APP 内列出的报告")
    ui = open(os.path.join("js", "ui.js"), encoding="utf-8").read()
    refs = re.findall(r"'(docs/[^']+\.md)'", ui)
    miss = [r for r in refs if not os.path.exists(r)]
    print(f"  代码引用 {len(refs)} 份；磁盘缺失 {len(miss)} 份" + (" ✅" if not miss else f" ❌ {miss}"))
    print(f"  磁盘 docs 实际 {len(os.listdir('docs'))} 份；已预缓存 "
          f"{sum(1 for x in listed if x.startswith('docs/'))} 份")

    ok = (not loaders) and (not ghost) and (not missing_rt) and (not miss)
    print("\n结论:", "✅ 完全自包含、可离线使用" if ok else "❌ 存在问题，见上")
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())

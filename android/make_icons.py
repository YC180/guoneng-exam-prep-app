#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""由应用自带的图标生成 Android 各密度图标（含 Android 8+ 自适应图标前景）。

输入：`D:\\DOWNLOADS\\app\\icons\\icon-512.png`（缺失时退回 icon-192.png）
输出：
  android/res/mipmap-{mdpi,hdpi,xhdpi,xxhdpi,xxxhdpi}/ic_launcher.png          48/72/96/144/192
  android/res/mipmap-{mdpi,hdpi,xhdpi,xxhdpi,xxxhdpi}/ic_launcher_foreground.png
                                                                              108/162/216/324/432
自适应图标规范：前景层画布为 108dp，安全区是居中 72dp（约 66%），
故前景图把原图标缩到约 62% 再居中，避免被系统圆形/方形遮罩裁掉边角。
"""
import os
import sys

from PIL import Image

APP_DIR = r"D:\DOWNLOADS\app"
RES = r"D:\app project\android\res"

DENSITIES = [
    ("mdpi", 1.0),
    ("hdpi", 1.5),
    ("xhdpi", 2.0),
    ("xxhdpi", 3.0),
    ("xxxhdpi", 4.0),
]
LAUNCHER_DP = 48
FOREGROUND_DP = 108
FOREGROUND_INSET = 0.62


def find_source():
    for name in ("icon-512.png", "icon-192.png", "icon.png"):
        p = os.path.join(APP_DIR, "icons", name)
        if os.path.isfile(p):
            return p
    raise SystemExit(f"❌ 未找到源图标（{APP_DIR}\\icons）")


def main():
    src_path = find_source()
    src = Image.open(src_path).convert("RGBA")
    print(f"源图标: {src_path}  {src.width}×{src.height}")
    made = 0
    for name, scale in DENSITIES:
        out_dir = os.path.join(RES, f"mipmap-{name}")
        os.makedirs(out_dir, exist_ok=True)

        # 传统图标（Android 7 及以下 / 部分启动器）
        size = int(round(LAUNCHER_DP * scale))
        icon = src.resize((size, size), Image.LANCZOS)
        icon.save(os.path.join(out_dir, "ic_launcher.png"), "PNG", optimize=True)
        made += 1

        # 自适应图标前景（透明画布 + 居中缩小的图标）
        canvas_size = int(round(FOREGROUND_DP * scale))
        inner = max(1, int(round(canvas_size * FOREGROUND_INSET)))
        fg = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
        small = src.resize((inner, inner), Image.LANCZOS)
        off = (canvas_size - inner) // 2
        fg.paste(small, (off, off), small)
        fg.save(os.path.join(out_dir, "ic_launcher_foreground.png"), "PNG", optimize=True)
        made += 1

    print(f"✅ 已生成 {made} 个图标文件（{len(DENSITIES)} 个密度 × 传统图标/自适应前景）")
    return 0


if __name__ == "__main__":
    sys.exit(main())

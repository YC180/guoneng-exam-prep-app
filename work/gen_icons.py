#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Generate PWA icons without any image library (pure zlib PNG writer).

Draws a dark navy rounded square with an amber energy bolt and a green
base arc, supersampled 3x for anti-aliasing.
"""
import os
import struct
import zlib

OUT = r"D:\DOWNLOADS\app\icons"
SS = 3                      # supersample factor

BG = (15, 23, 42)           # #0f172a
BG2 = (30, 41, 59)          # #1e293b
BOLT = (245, 158, 11)       # #f59e0b
BOLT2 = (252, 211, 77)      # #fcd34d
GREEN = (16, 185, 129)      # #10b981

# 闪电多边形（单位坐标）
BOLT_PTS = [(0.60, 0.06), (0.26, 0.56), (0.45, 0.56), (0.38, 0.94),
            (0.74, 0.42), (0.53, 0.42)]


def in_poly(x, y, pts):
    inside = False
    n = len(pts)
    j = n - 1
    for i in range(n):
        xi, yi = pts[i]
        xj, yj = pts[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi):
            inside = not inside
        j = i
    return inside


def rounded_alpha(x, y, r):
    """1.0 inside the rounded square, 0.0 outside (unit coords)."""
    cx = min(max(x, r), 1 - r)
    cy = min(max(y, r), 1 - r)
    dx, dy = x - cx, y - cy
    d = (dx * dx + dy * dy) ** 0.5
    if d <= r:
        return 1.0
    return 0.0


def render(size):
    W = size * SS
    r = 0.22
    rows = []
    for py in range(W):
        row = bytearray()
        for px in range(W):
            x = (px + 0.5) / W
            y = (py + 0.5) / W
            a = rounded_alpha(x, y, r)
            if a <= 0:
                row += bytes((0, 0, 0, 0))
                continue
            # 背景：左上到右下渐变
            t = (x + y) / 2
            col = tuple(int(BG[i] + (BG2[i] - BG[i]) * t) for i in range(3))
            # 底部弧（绿色能量基座）
            arc_y = 0.845 + 0.045 * ((x - 0.5) ** 2) * 4
            if y > arc_y and y < arc_y + 0.062:
                col = GREEN
            # 闪电
            if in_poly(x, y, BOLT_PTS):
                col = BOLT2 if (x < 0.5) else BOLT
            row += bytes((col[0], col[1], col[2], int(a * 255)))
        rows.append(bytes(row))
    return rows


def downsample(rows, size):
    W = size * SS
    out = []
    for py in range(size):
        row = bytearray()
        for px in range(size):
            acc = [0, 0, 0, 0]
            for dy in range(SS):
                src = rows[py * SS + dy]
                for dx in range(SS):
                    o = (px * SS + dx) * 4
                    for c in range(4):
                        acc[c] += src[o + c]
            n = SS * SS
            row += bytes((acc[0] // n, acc[1] // n, acc[2] // n, acc[3] // n))
        out.append(bytes(row))
    return out


def write_png(path, size, rows):
    raw = b"".join(b"\x00" + r for r in rows)

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
           + chunk(b"IDAT", zlib.compress(raw, 9))
           + chunk(b"IEND", b""))
    with open(path, "wb") as fh:
        fh.write(png)
    return len(png)


def main():
    os.makedirs(OUT, exist_ok=True)
    for size in (192, 512):
        rows = downsample(render(size), size)
        p = os.path.join(OUT, f"icon-{size}.png")
        n = write_png(p, size, rows)
        print(f"{p}  {size}x{size}  {n / 1024:.1f} KB")

    svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" role="img" aria-label="国家能源集团备考学习">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#0f172a"/><stop offset="1" stop-color="#1e293b"/>
    </linearGradient>
    <linearGradient id="bolt" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#fcd34d"/><stop offset="1" stop-color="#f59e0b"/>
    </linearGradient>
  </defs>
  <rect width="512" height="512" rx="113" fill="url(#bg)"/>
  <path d="M307 31 L133 287 L230 287 L195 481 L379 215 L271 215 Z" fill="url(#bolt)"/>
  <path d="M96 433 q160 62 320 0 v32 q-160 62 -320 0 z" fill="#10b981"/>
</svg>
'''
    p = os.path.join(OUT, "icon.svg")
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(svg)
    print(p)


if __name__ == "__main__":
    main()

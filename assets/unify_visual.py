# -*- coding: utf-8 -*-
"""统一切换观感：
1) 123 帧视频帧轻度锐化（透明区先填充主体平均色，避免锐化黑边）；
2) main/doze 水平拉伸对齐视频帧坐姿宽度(410)，消除切换"变宽"。
"""
import os
from PIL import Image, ImageFilter

FRAMES = r"F:\AI产物\doubao\deskpet\assets\frames"

# ---------- 1) 视频帧锐化 ----------
for i in range(1, 124):
    p = os.path.join(FRAMES, f"model_sleep_full_{i:03d}.png")
    im = Image.open(p).convert("RGBA")
    r, g, b, a = im.split()
    # 主体平均色（用于填充透明区，隔离锐化对边缘的影响）
    am = a.point(lambda v: 255 if v >= 128 else 0)
    npx = sum(am.getdata())
    if npx:
        rs = sum(px * (1 if m else 0) for px, m in zip(r.getdata(), am.getdata())) // npx
        gs = sum(px * (1 if m else 0) for px, m in zip(g.getdata(), am.getdata())) // npx
        bs = sum(px * (1 if m else 0) for px, m in zip(b.getdata(), am.getdata())) // npx
    else:
        rs, gs, bs = 200, 170, 120
    rgb = Image.merge("RGB", (r, g, b))
    rgb2 = rgb.copy()
    rgb2.paste((rs, gs, bs), mask=a.point(lambda v: 255 if v < 128 else 0).convert("L"))
    sharp = rgb2.filter(ImageFilter.UnsharpMask(radius=1.5, percent=80, threshold=2))
    out = sharp.convert("RGBA")
    out.putalpha(a)
    out.save(p)
print("video frames sharpened")

# ---------- 2) main/doze 宽高对齐视频帧坐姿 (410 x 577)，消除切换"变宽/变高" ----------
CANVAS, T_BOTTOM, T_CX = 720, 690, 383
TARGET_W, TARGET_H = 410, 577
for n in ("model_main", "model_doze"):
    p = os.path.join(FRAMES, n + ".png")
    im = Image.open(p).convert("RGBA")
    am = im.getchannel("A").point(lambda v: 255 if v >= 128 else 0)
    bb = am.getbbox()
    crop = im.crop(bb)
    im2 = crop.resize((TARGET_W, TARGET_H), Image.LANCZOS)   # 非等比（横向仅 +6.5%）
    dx = T_CX - TARGET_W // 2
    dy = T_BOTTOM - TARGET_H
    canvas = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    canvas.paste(im2, (dx, dy), im2)
    b2 = canvas.getchannel("A").point(lambda v: 255 if v >= 128 else 0).getbbox()
    canvas.save(p)
    print(n, "new size", TARGET_W, "x", TARGET_H, "at", (dx, dy), "bbox", b2)
print("done")

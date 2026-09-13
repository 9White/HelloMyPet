# -*- coding: utf-8 -*-
"""重建 123 帧：清边 -> 稳定化 -> 毛色对齐主形象 -> 轻锐化一次（消除画质/颜色突变）
源：sleep_full_cut（抠图产物）；输出：frames/model_sleep_full_XXX.png
"""
import os
import sys

sys.path.insert(0, r"F:\AI产物\doubao\deskpet")
from PIL import Image, ImageFilter, ImageChops

from pet import clean_edges

CUT = r"F:\AI产物\doubao\deskpet\assets\video_frames\sleep_full_cut"
FRAMES = r"F:\AI产物\doubao\deskpet\assets\frames"
TARGET = (178, 152, 117)     # 主形象 model_main 主体平均毛色
T_BOTTOM, T_CX = 690, 383
CANVAS = 720


def avg_rgb(im, am):
    N = sum(1 for m in am.getdata() if m)
    r, g, b, _ = im.split()
    ar = sum(px for px, m in zip(r.getdata(), am.getdata()) if m) // N
    ag = sum(px for px, m in zip(g.getdata(), am.getdata()) if m) // N
    ab = sum(px for px, m in zip(b.getdata(), am.getdata()) if m) // N
    return ar, ag, ab


for i in range(1, 124):
    im = Image.open(os.path.join(CUT, f"n{i:03d}.png")).convert("RGBA")
    im = clean_edges(im)
    # 稳定化：主体底部中心对齐
    am = im.getchannel("A").point(lambda v: 255 if v >= 128 else 0)
    bb = am.getbbox()
    dx = T_CX - (bb[0] + bb[2]) // 2
    dy = T_BOTTOM - bb[3]
    canvas = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    canvas.paste(im, (dx, dy), im)
    im = clean_edges(canvas)

    # 毛色对齐：per-channel 增益 -> 主形象平均色
    r, g, b, a = im.split()
    am = a.point(lambda v: 255 if v >= 128 else 0)
    avg = avg_rgb(im, am)
    sr = min(1.3, max(0.7, TARGET[0] / avg[0]))
    sg = min(1.3, max(0.7, TARGET[1] / avg[1]))
    sb = min(1.3, max(0.7, TARGET[2] / avg[2]))
    r = r.point(lambda v: min(255, int(v * sr)))
    g = g.point(lambda v: min(255, int(v * sg)))
    b = b.point(lambda v: min(255, int(v * sb)))

    # 轻锐化一次（透明区填主形象毛色隔离，防黑边）
    rgb = Image.merge("RGB", (r, g, b))
    rgb2 = rgb.copy()
    rgb2.paste(TARGET, mask=a.point(lambda v: 255 if v < 128 else 0).convert("L"))
    sharp = rgb2.filter(ImageFilter.UnsharpMask(radius=1.0, percent=45, threshold=3))
    out = sharp.convert("RGBA")
    out.putalpha(a)
    out.save(os.path.join(FRAMES, f"model_sleep_full_{i:03d}.png"))
    if i % 10 == 0:
        print(i, "avg", avg, "scale", (round(sr, 3), round(sg, 3), round(sb, 3)), flush=True)
print("done")

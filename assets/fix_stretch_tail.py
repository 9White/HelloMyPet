# -*- coding: utf-8 -*-
"""伸展帧顶部余量：顶边 < 28 的帧整体下移，使尾巴尖完整（含羽化空间）"""
import os

from PIL import Image

FRAMES = r"F:\AI产物\doubao\deskpet\assets\frames"
TOP_MIN = 20  # 目标顶边（画布坐标），保留羽化余量


def fix(p):
    im = Image.open(p).convert("RGBA")
    a = im.split()[3]
    am = a.point(lambda v: 255 if v >= 40 else 0)
    bb = am.getbbox()
    if bb is None or bb[1] >= 40:
        return False  # 只处理贴顶的伸展帧，端坐帧保持与主形象对齐
    dy = TOP_MIN - bb[1]
    canvas = Image.new("RGBA", im.size, (0, 0, 0, 0))
    canvas.paste(im, (0, dy), im)
    canvas.save(p)
    return dy


n = 0
for i in range(1, 124):
    p = os.path.join(FRAMES, "model_stretch_full_%03d.png" % i)
    dy = fix(p)
    if dy:
        n += 1
        if n <= 12:
            print("shift", i, dy, flush=True)
print("shifted", n, "frames")

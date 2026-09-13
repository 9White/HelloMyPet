# -*- coding: utf-8 -*-
"""主形象帧二次统一：裁掉留白 + 猫主体高度对齐视频帧坐姿(577px)，地面线一致(690)
解决：点击睡觉瞬间猫"先变大"（视频帧猫比主形象大 25%）。
从备份原图(675x900)重做；123 帧视频序列不动。"""
import os
import shutil
from PIL import Image, ImageChops

SRC = r"F:\AI产物\doubao\deskpet\assets\frames"
BAK = r"F:\AI产物\doubao\deskpet\assets\frames_bak_720"
os.makedirs(BAK, exist_ok=True)
DST = r"F:\AI产物\doubao\deskpet\assets\frames"
CANVAS = 720
T_H = 577        # 目标主体高度（= 视频帧坐姿 n001 的 bbox 高）
T_BOTTOM = 690   # 地面线
T_CX = 383
MAX_W = 700

NAMES = ["model_main", "model_doze", "model_side_stand", "model_walk_l",
         "model_walk_r", "model_stretch_arch", "model_stretch_reach",
         "model_stretch_flat", "model_look_l", "model_look_r",
         "model_lie_side", "model_sleep_curl", "model_jump_crouch",
         "model_jump_air"]


def clean_edges(im):
    r, g, b, a = im.split()
    sum_rgb = ImageChops.add(ImageChops.add(r, g), b)
    dark = sum_rgb.point(lambda v: 255 if v < 180 else 0)
    semi = a.point(lambda v: 255 if 0 < v < 245 else 0)
    a = ImageChops.subtract(a, ImageChops.multiply(dark, semi))
    a = a.point(lambda v: 255 if v >= 96 else 0)
    return Image.merge("RGBA", (r, g, b, a))


for n in NAMES:
    im = Image.open(os.path.join(SRC, n + ".png")).convert("RGBA")
    shutil.copy(os.path.join(SRC, n + ".png"), os.path.join(BAK, n + ".png"))
    a = im.getchannel("A")
    m = a.point(lambda v: 255 if v >= 128 else 0)
    bb = m.getbbox()
    bb_h, bb_w = bb[3] - bb[1], bb[2] - bb[0]

    # 裁剪到主体（上下左右各留 4px 余量）
    crop = im.crop((max(0, bb[0] - 4), max(0, bb[1] - 4),
                    min(im.width, bb[2] + 4), min(im.height, bb[3] + 4)))
    cw, ch = crop.size

    if n == "model_jump_air":
        bottom = 388          # 腾空帧：保持离地高度，不落地
    else:
        bottom = T_BOTTOM
    scale = min(T_H / ch, MAX_W / cw, 10)
    if n == "model_jump_air":
        scale = min(scale, bottom / ch)     # 顶部不能越界
    nw, nh = round(cw * scale), round(ch * scale)

    im2 = crop.resize((nw, nh), Image.LANCZOS)
    im2 = clean_edges(im2)
    dx = T_CX - nw // 2
    dy = bottom - nh
    canvas = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    canvas.paste(im2, (dx, dy), im2)
    a2 = canvas.getchannel("A")
    b2 = a2.point(lambda v: 255 if v >= 128 else 0).getbbox()
    if b2 and (b2[0] < 0 or b2[1] < 0 or b2[2] > CANVAS or b2[3] > CANVAS):
        print("OUT", n, b2)
        continue
    canvas.save(os.path.join(DST, n + ".png"))
    print(f"{n}: src_bbox_h={bb_h} scale={scale:.3f} -> {nw}x{nh} at ({dx},{dy}) bbox={b2}")
print("done")

# -*- coding: utf-8 -*-
"""第二版主形象睡觉视频 148 帧最终后处理：
1) 软边(清暗半透明+alpha羽化) 2) 统一体型归位(坐姿->523x577 与主形象一致)
3) 稳定化(底690/中383) 4) 毛色统一(178,152,117) 5) 轻锐化
另：main/doze 拉伸到 523x577（宽扁体型，与设定图一致）
"""
import os

from PIL import Image, ImageChops, ImageFilter

CUT = r"F:\AI产物\doubao\deskpet\assets\video_frames\main_sleep2_cut"
FRAMES = r"F:\AI产物\doubao\deskpet\assets\frames"
T_BOTTOM, T_CX = 690, 383
CANVAS = 720
TARGET = (178, 152, 117)
MAIN_W, MAIN_H = 523, 577          # 主形象坐姿目标尺寸（设定图 0.906 宽扁体型）


def soft_edges(im):
    r, g, b, a = im.split()
    sum_rgb = ImageChops.add(ImageChops.add(r, g), b)
    dark = sum_rgb.point(lambda v: 255 if v < 180 else 0)
    semi = a.point(lambda v: 255 if 0 < v < 245 else 0)
    a = ImageChops.subtract(a, ImageChops.multiply(dark, semi))
    a = a.filter(ImageFilter.GaussianBlur(0.5))
    return Image.merge("RGBA", (r, g, b, a))


def avg_rgb(im, am):
    N = sum(1 for m in am.getdata() if m)
    r, g, b, _ = im.split()
    return (sum(px for px, m in zip(r.getdata(), am.getdata()) if m) // N,
            sum(px for px, m in zip(g.getdata(), am.getdata()) if m) // N,
            sum(px for px, m in zip(b.getdata(), am.getdata()) if m) // N)


# ---- 第一步：测 f001 坐姿 bbox，定统一缩放 ----
f1 = soft_edges(Image.open(os.path.join(CUT, "f001.png")).convert("RGBA"))
am1 = f1.getchannel("A").point(lambda v: 255 if v >= 128 else 0)
bb1 = am1.getbbox()
print("f001 bbox", bb1, "->", (bb1[2]-bb1[0], bb1[3]-bb1[1]))
sw = MAIN_W / (bb1[2] - bb1[0])
sh = MAIN_H / (bb1[3] - bb1[1])
print("scale", sw, sh)

# ---- 第二步：处理 148 帧 ----
imgs, avgs = [], []
for i in range(1, 149):
    im = soft_edges(Image.open(os.path.join(CUT, f"f{i:03d}.png")).convert("RGBA"))
    w, h = round(im.width * sw), round(im.height * sh)
    im = im.resize((w, h), Image.LANCZOS)
    am = im.getchannel("A").point(lambda v: 255 if v >= 128 else 0)
    bb = am.getbbox()
    dx = T_CX - (bb[0] + bb[2]) // 2
    dy = T_BOTTOM - bb[3]
    canvas = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    canvas.paste(im, (dx, dy), im)
    imgs.append(canvas)
    avgs.append(avg_rgb(canvas, canvas.getchannel("A").point(
        lambda v: 255 if v >= 128 else 0)))

total = tuple(sum(a[k] for a in avgs) // len(avgs) for k in range(3))
gain = tuple(min(1.8, max(0.7, TARGET[k] / total[k])) for k in range(3))
print("total avg", total, "gain", gain)

for i, canvas in enumerate(imgs, 1):
    r, g, b, a = canvas.split()
    r = r.point(lambda v, s=gain[0]: min(255, int(v * s)))
    g = g.point(lambda v, s=gain[1]: min(255, int(v * s)))
    b = b.point(lambda v, s=gain[2]: min(255, int(v * s)))
    rgb = Image.merge("RGB", (r, g, b))
    rgb2 = rgb.copy()
    rgb2.paste(TARGET, mask=a.point(lambda v: 255 if v < 128 else 0).convert("L"))
    sharp = rgb2.filter(ImageFilter.UnsharpMask(radius=1.0, percent=40, threshold=3))
    out = sharp.convert("RGBA")
    out.putalpha(a)
    out.save(os.path.join(FRAMES, f"model_sleep_full_{i:03d}.png"))
    if i % 30 == 0:
        print(i, flush=True)

# ---- 第三步：main/doze 拉伸到 523x577 ----
for name in ("model_main.png", "model_doze.png"):
    p = os.path.join(FRAMES, name)
    im = Image.open(p).convert("RGBA")
    im = im.resize((MAIN_W, MAIN_H), Image.LANCZOS)
    im.save(p)
    print(name, "->", MAIN_W, MAIN_H)
print("done")

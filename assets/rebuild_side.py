# -*- coding: utf-8 -*-
"""侧躺视频 99 帧入库：等比例对齐主形象（高 575）、720 画布中心 383 底边 690、
逐帧增益平滑、轻锐化、半透明区填毛色。输出 frames/model_side_full_001~099.png。"""
import os

from PIL import Image, ImageChops, ImageFilter

CUT = r"F:\AI产物\doubao\deskpet\assets\video_frames\user_side_cut"
FRAMES = r"F:\AI产物\doubao\deskpet\assets\frames"
TARGET = (178, 152, 117)
T_BOTTOM, T_CX = 690, 383
T_H = 575  # 主形象高度


def soft_edges(im):
    r, g, b, a = im.split()
    sum_rgb = ImageChops.add(ImageChops.add(r, g), b)
    dark = sum_rgb.point(lambda v: 255 if v < 180 else 0)
    semi = a.point(lambda v: 255 if 0 < v < 245 else 0)
    a = ImageChops.subtract(a, ImageChops.multiply(dark, semi))
    a = a.filter(ImageFilter.GaussianBlur(0.5))
    return Image.merge("RGBA", (r, g, b, a))


# 以首帧主体为基准，等比例缩放到高度 T_H
f1 = Image.open(os.path.join(CUT, "u001.png")).convert("RGBA")
bb1 = f1.getchannel("A").point(lambda v: 255 if v >= 128 else 0).getbbox()
S = T_H / (bb1[3] - bb1[1])
print("scale", round(S, 4), "bbox1", bb1)

imgs, gains = [], []
for i in range(1, 100):
    im = soft_edges(Image.open(os.path.join(CUT, f"u{i:03d}.png")).convert("RGBA"))
    im = im.resize((round(im.width * S), round(im.height * S)), Image.LANCZOS)
    canvas = Image.new("RGBA", (720, 720), (0, 0, 0, 0))
    am = im.getchannel("A").point(lambda v: 255 if v >= 128 else 0)
    bb = am.getbbox()
    dx = T_CX - (bb[0] + bb[2]) // 2
    dy = T_BOTTOM - bb[3]
    canvas.paste(im, (dx, dy), im)
    im = canvas
    imgs.append(im)
    r, g, b, a = im.split()
    am = a.point(lambda v: 255 if v >= 128 else 0)
    N = sum(1 for m in am.getdata() if m)
    av = [sum(px for px, m in zip(c.getdata(), am.getdata()) if m) // N for c in (r, g, b)]
    gains.append(tuple(min(1.8, max(0.7, TARGET[k] / av[k])) for k in range(3)))

smooth = []
for i in range(len(gains)):
    seg = gains[max(0, i - 3):min(len(gains), i + 4)]
    smooth.append(tuple(sum(s[k] for s in seg) / len(seg) for k in range(3)))
print("gain R", round(min(g[0] for g in gains), 3), round(max(g[0] for g in gains), 3))

for i, im in enumerate(imgs, 1):
    r, g, b, a = im.split()
    gain = smooth[i - 1]
    r = r.point(lambda v, s=gain[0]: min(255, int(v * s)))
    g = g.point(lambda v, s=gain[1]: min(255, int(v * s)))
    b = b.point(lambda v, s=gain[2]: min(255, int(v * s)))
    rgb = Image.merge("RGB", (r, g, b))
    rgb2 = rgb.copy()
    rgb2.paste(TARGET, mask=a.point(lambda v: 255 if v < 128 else 0).convert("L"))
    sharp = rgb2.filter(ImageFilter.UnsharpMask(radius=1.0, percent=40, threshold=3)).convert("RGBA")
    sharp.putalpha(a)
    sharp.save(os.path.join(FRAMES, f"model_side_full_{i:03d}.png"))
    if i % 30 == 0:
        print(i, flush=True)
print("done")

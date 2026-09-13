# -*- coding: utf-8 -*-
"""用户视频 123 帧入库：统一缩放对齐 model_main（382x575）、稳定化、
逐帧增益平滑、轻锐化。覆写 model_sleep_full_001~123.png（并清理 124~148 旧帧）。"""
import os

from PIL import Image, ImageChops, ImageFilter

CUT = r"F:\AI产物\doubao\deskpet\assets\video_frames\user_sleep_cut"
FRAMES = r"F:\AI产物\doubao\deskpet\assets\frames"
TARGET = (178, 152, 117)
T_BOTTOM, T_CX = 690, 383
SX, SY = 382 / 408, 575 / 576


def soft_edges(im):
    r, g, b, a = im.split()
    sum_rgb = ImageChops.add(ImageChops.add(r, g), b)
    dark = sum_rgb.point(lambda v: 255 if v < 180 else 0)
    semi = a.point(lambda v: 255 if 0 < v < 245 else 0)
    a = ImageChops.subtract(a, ImageChops.multiply(dark, semi))
    a = a.filter(ImageFilter.GaussianBlur(0.5))
    return Image.merge("RGBA", (r, g, b, a))


imgs, gains = [], []
for i in range(1, 124):
    im = soft_edges(Image.open(os.path.join(CUT, f"u{i:03d}.png")).convert("RGBA"))
    im = im.resize((round(im.width * SX), round(im.height * SY)), Image.LANCZOS)
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
    sharp.save(os.path.join(FRAMES, f"model_sleep_full_{i:03d}.png"))
    if i % 40 == 0:
        print(i, flush=True)

# 清理 124~148 旧帧
for i in range(124, 149):
    p = os.path.join(FRAMES, f"model_sleep_full_{i:03d}.png")
    if os.path.exists(p):
        os.remove(p)
print("done")

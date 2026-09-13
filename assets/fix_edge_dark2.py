# -*- coding: utf-8 -*-
"""去边缘黑线 v2：仅清除半透明暗像素 + 0.7 轻羽化平滑（不收缩、不重羽化）。"""
import os

from PIL import Image, ImageFilter

FRAMES = r"F:\AI产物\doubao\deskpet\assets\frames"

TARGETS = ["model_main.png", "model_doze.png"]
TARGETS += [f"model_sleep_full_{i:03d}.png" for i in range(1, 124)]


def clean(im):
    r, g, b, a = im.split()
    pr, pg, pb, pa = [x.getdata() for x in (r, g, b, a)]
    na = [0 if (0 < A < 245 and (R + G + B) < 260) else A
          for R, G, B, A in zip(pr, pg, pb, pa)]
    a = Image.new("L", im.size)
    a.putdata(na)
    a = a.filter(ImageFilter.GaussianBlur(0.7))
    out = Image.merge("RGBA", (r, g, b, a))
    return out


def count_dark_edge(im):
    pr, pg, pb, pa = [x.getdata() for x in im.split()]
    return sum(1 for R, G, B, A in zip(pr, pg, pb, pa) if 0 < A < 245 and (R + G + B) < 260)


def bbox(im):
    return im.getchannel("A").point(lambda v: 255 if v >= 128 else 0).getbbox()


for f in TARGETS:
    p = os.path.join(FRAMES, f)
    im = Image.open(p).convert("RGBA")
    before = count_dark_edge(im)
    bb0 = bbox(im)
    out = clean(im)
    after = count_dark_edge(out)
    bb1 = bbox(out)
    out.save(p)
    print(f, before, "->", after,
          (bb1[2]-bb1[0], bb1[3]-bb1[1]), "vs", (bb0[2]-bb0[0], bb0[3]-bb0[1]))
print("done")

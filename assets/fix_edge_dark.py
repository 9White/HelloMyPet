# -*- coding: utf-8 -*-
"""去边缘黑线：清除半透明暗像素 + alpha 收缩 1px 羽化。应用全部帧。"""
import os

from PIL import Image, ImageFilter

FRAMES = r"F:\AI产物\doubao\deskpet\assets\frames"

TARGETS = ["model_main.png", "model_doze.png"]
TARGETS += [f"model_sleep_full_{i:03d}.png" for i in range(1, 124)]
for f in ["model_side_stand.png", "model_walk_l.png", "model_walk_r.png",
          "model_stretch_arch.png", "model_stretch_reach.png", "model_stretch_flat.png",
          "model_look_l.png", "model_look_r.png", "model_lie_side.png",
          "model_sleep_curl.png", "model_jump_crouch.png", "model_jump_air.png"]:
    TARGETS.append(f)


def clean(im):
    r, g, b, a = im.split()
    pr, pg, pb, pa = [x.getdata() for x in (r, g, b, a)]
    # 半透明且暗 → 完全透明
    na = [0 if (0 < A < 245 and (R + G + B) < 260) else A
          for R, G, B, A in zip(pr, pg, pb, pa)]
    a = Image.new("L", im.size)
    a.putdata(na)
    # 收缩 1px 削掉残余边缘，再羽化
    a = a.filter(ImageFilter.MinFilter(3))
    a = a.filter(ImageFilter.GaussianBlur(1.2))
    out = Image.merge("RGBA", (r, g, b, a))
    return out


def count_dark_edge(im):
    pr, pg, pb, pa = [x.getdata() for x in im.split()]
    return sum(1 for R, G, B, A in zip(pr, pg, pb, pa) if 0 < A < 245 and (R + G + B) < 260)


for f in TARGETS:
    p = os.path.join(FRAMES, f)
    if not os.path.exists(p):
        print("MISS", f)
        continue
    im = Image.open(p).convert("RGBA")
    before = count_dark_edge(im)
    out = clean(im)
    after = count_dark_edge(out)
    out.save(p)
    print(f, before, "->", after)
print("done")

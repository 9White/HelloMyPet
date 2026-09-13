# -*- coding: utf-8 -*-
"""素材层：清除边界不透明极暗点（邻域透明 + 亮度<330 → alpha 0）。全部帧。"""
import os

from PIL import Image, ImageFilter

FRAMES = r"F:\AI产物\doubao\deskpet\assets\frames"
FILES = ["model_main.png", "model_doze.png"] + \
        [f"model_sleep_full_{i:03d}.png" for i in range(1, 124)] + \
        ["model_side_stand.png", "model_walk_l.png", "model_walk_r.png",
         "model_stretch_arch.png", "model_stretch_reach.png", "model_stretch_flat.png",
         "model_look_l.png", "model_look_r.png", "model_lie_side.png",
         "model_sleep_curl.png", "model_jump_crouch.png", "model_jump_air.png"]


def fix(p):
    im = Image.open(p).convert("RGBA")
    r, g, b, a = im.split()
    amin = a.filter(ImageFilter.MinFilter(3))
    edge = amin.point(lambda v: 255 if v == 0 else 0)  # 邻域有透明
    pe = list(edge.getdata())
    pr, pg, pb, pa = (list(x.getdata()) for x in (r, g, b, a))
    n = 0
    for i, e in enumerate(pe):
        if e and pa[i] > 0 and (pr[i] + pg[i] + pb[i]) < 330:
            pa[i] = 0
            n += 1
    if n:
        a.putdata(pa)
        out = Image.merge("RGBA", (r, g, b, a))
        out.save(p)
    return n


tot = 0
for f in FILES:
    p = os.path.join(FRAMES, f)
    if os.path.exists(p):
        n = fix(p)
        if n:
            print(f, "cleared", n)
        tot += n
print("total cleared:", tot)

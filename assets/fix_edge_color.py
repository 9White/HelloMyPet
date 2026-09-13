# -*- coding: utf-8 -*-
"""边缘去虚：半透明边缘像素颜色染为邻域真实毛色 + 清除超淡断点 alpha。
效果：轮廓直接就是毛发色，桌面（含深色）上无黑线、无虚线。全部帧处理。"""
import os

from PIL import Image

FRAMES = r"F:\AI产物\doubao\deskpet\assets\frames"
CLEAR_A = 45      # alpha 低于此值的边缘像素清为透明（断点）
COLOR_A = 250     # alpha 低于此值的半透明像素染邻域毛色（含 250-254 的轻微羽化）


def fix(p):
    im = Image.open(p).convert("RGBA")
    r, g, b, a = im.split()
    pr, pg, pb, pa = (list(x.getdata()) for x in (r, g, b, a))
    W, H = im.size
    n_del = n_color = 0
    for y in range(H):
        for x in range(W):
            i = y * W + x
            A = pa[i]
            if A == 0 or A >= COLOR_A:
                continue
            # 只处理边缘像素：4 邻域存在透明（轮廓过渡带）
            edge = (y > 0 and pa[i - W] == 0) or (y < H - 1 and pa[i + W] == 0) \
                or (x > 0 and pa[i - 1] == 0) or (x < W - 1 and pa[i + 1] == 0)
            if not edge:
                continue
            # 邻域（3x3，排除自身）非透明像素平均色
            sR = sG = sB = n = 0
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < W and 0 <= ny < H:
                        j = ny * W + nx
                        if pa[j] > 0:
                            sR += pr[j]; sG += pg[j]; sB += pb[j]; n += 1
            if A < CLEAR_A:
                pa[i] = 0
                n_del += 1
            elif n:
                # 染为邻域真实毛色（保留羽化渐变）
                pr[i] = sR // n; pg[i] = sG // n; pb[i] = sB // n
                n_color += 1
    if n_del or n_color:
        r.putdata(pr); g.putdata(pg); b.putdata(pb); a.putdata(pa)
        Image.merge("RGBA", (r, g, b, a)).save(p)
    return n_del, n_color


tot_d = tot_c = 0
for f in sorted(os.listdir(FRAMES)):
    if f.lower().endswith(".png"):
        d, c = fix(os.path.join(FRAMES, f))
        if d or c:
            print(f, "del", d, "color", c)
        tot_d += d; tot_c += c
print("TOTAL del", tot_d, "color", tot_c)

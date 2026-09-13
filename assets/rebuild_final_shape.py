# -*- coding: utf-8 -*-
"""体型纠正版：main/doze 用新生成的匀称侧面端坐帧；视频 148 帧统一到 410x577；
逐帧增益平滑消除变色。全部软边 + 稳定化 + 轻锐化。
"""
import os

from PIL import Image, ImageChops, ImageFilter

FRAMES = r"F:\AI产物\doubao\deskpet\assets\frames"
CUT = r"F:\AI产物\doubao\deskpet\assets\video_frames\main_sleep2_cut"
T_BOTTOM, T_CX = 690, 383
CANVAS = 720
TARGET = (178, 152, 117)
MAIN_W, MAIN_H = 410, 577     # 匀称体型（与 cat_model_v1 视觉一致，不扁）


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


def fit(im, w, h):
    """等比缩放内容使高=h、宽不超过 w，再轻微横向归位到 w"""
    am = im.getchannel("A").point(lambda v: 255 if v >= 128 else 0)
    bb = am.getbbox()
    scale = min(w / (bb[2] - bb[0]), h / (bb[3] - bb[1]))
    im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
    am = im.getchannel("A").point(lambda v: 255 if v >= 128 else 0)
    bb = am.getbbox()
    if (bb[2] - bb[0]) < w - 2:
        # 横向轻微拉伸补足宽度（<1.5% 无感）
        nw = w - (bb[2] - bb[0])
        im = im.resize((im.width + nw, im.height), Image.LANCZOS)
    canvas = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    am = im.getchannel("A").point(lambda v: 255 if v >= 128 else 0)
    bb = am.getbbox()
    dx = T_CX - (bb[0] + bb[2]) // 2
    dy = T_BOTTOM - bb[3]
    canvas.paste(im, (dx, dy), im)
    return canvas


def colorize(im, gain):
    r, g, b, a = im.split()
    r = r.point(lambda v, s=gain[0]: min(255, int(v * s)))
    g = g.point(lambda v, s=gain[1]: min(255, int(v * s)))
    b = b.point(lambda v, s=gain[2]: min(255, int(v * s)))
    rgb = Image.merge("RGB", (r, g, b))
    rgb2 = rgb.copy()
    rgb2.paste(TARGET, mask=a.point(lambda v: 255 if v < 128 else 0).convert("L"))
    sharp = rgb2.filter(ImageFilter.UnsharpMask(radius=1.0, percent=40, threshold=3))
    out = sharp.convert("RGBA")
    out.putalpha(a)
    return out


# ---- 1. main / doze 重新入库（匀称体型） ----
for src, name in ((r"F:\AI产物\doubao\deskpet\assets\main_new_cut.png", "model_main.png"),
                  (r"F:\AI产物\doubao\deskpet\assets\doze_new_cut.png", "model_doze.png")):
    im = soft_edges(Image.open(src).convert("RGBA"))
    im = fit(im, MAIN_W, MAIN_H)
    r, g, b, a = im.split()
    am = a.point(lambda v: 255 if v >= 128 else 0)
    avg = avg_rgb(im, am)
    gain = tuple(min(1.8, max(0.7, TARGET[k] / avg[k])) for k in range(3))
    out = colorize(im, gain)
    out.save(os.path.join(FRAMES, name))
    print(name, "bbox", a.point(lambda v: 255 if v >= 128 else 0).getbbox(),
          "gain", [round(x, 3) for x in gain])

# ---- 2. 视频 148 帧：统一缩放 + 稳定化 + 逐帧增益平滑 ----
# 先缩放稳定化并收集每帧增益
imgs, gains = [], []
for i in range(1, 149):
    im = soft_edges(Image.open(os.path.join(CUT, f"f{i:03d}.png")).convert("RGBA"))
    im = fit(im, MAIN_W, MAIN_H)
    imgs.append(im)
    r, g, b, a = im.split()
    am = a.point(lambda v: 255 if v >= 128 else 0)
    avg = avg_rgb(im, am)
    gains.append(tuple(min(1.8, max(0.7, TARGET[k] / avg[k])) for k in range(3)))
print("gain range R", min(g[0] for g in gains), max(g[0] for g in gains))

# 移动平均平滑（窗口 7）
smooth = []
for i in range(len(gains)):
    lo = max(0, i - 3)
    hi = min(len(gains), i + 4)
    seg = gains[lo:hi]
    smooth.append(tuple(sum(s[k] for s in seg) / len(seg) for k in range(3)))

for i, im in enumerate(imgs, 1):
    out = colorize(im, smooth[i - 1])
    out.save(os.path.join(FRAMES, f"model_sleep_full_{i:03d}.png"))
    if i % 30 == 0:
        print(i, flush=True)
print("done")

# -*- coding: utf-8 -*-
"""帧稳定化：按主体 bbox 底部中心对齐所有帧，消除 AI 视频逐帧位置抖动"""
import os
from PIL import Image

FRAMES = r"F:\AI产物\doubao\deskpet\assets\frames"
N = 123

boxes = []
for i in range(1, N + 1):
    im = Image.open(os.path.join(FRAMES, f"model_sleep_full_{i:03d}.png")).convert("RGBA")
    a = im.getchannel("A")
    # 不透明像素 bbox（alpha>=128）
    bb = a.point(lambda v: 255 if v >= 128 else 0).getbbox()
    boxes.append(bb)

# 底部中心：取各帧 bbox 底部 y 与中心 x 的中位数（抗个别异常帧）
bots = sorted(b[3] for b in boxes)
cents = sorted((b[0] + b[2]) // 2 for b in boxes)
target_bottom = bots[len(bots) // 2]
target_cx = cents[len(cents) // 2]
print("target bottom", target_bottom, "target cx", target_cx)

clips = []
for i in range(1, N + 1):
    im = Image.open(os.path.join(FRAMES, f"model_sleep_full_{i:03d}.png")).convert("RGBA")
    b = boxes[i - 1]
    dx = target_cx - (b[0] + b[2]) // 2
    dy = target_bottom - b[3]
    canvas = Image.new("RGBA", im.size, (0, 0, 0, 0))
    canvas.paste(im, (dx, dy), im)
    if dx < 0 or dy < 0:
        clips.append(i)
    canvas.save(os.path.join(FRAMES, f"model_sleep_full_{i:03d}.png"))
print("clipped frames:", clips)
print("done")

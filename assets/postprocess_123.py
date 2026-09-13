# -*- coding: utf-8 -*-
"""123 帧抠图产物后处理：clean_edges 二值化清边 + 保存到 frames/ 素材库"""
import os
import sys

sys.path.insert(0, r"F:\AI产物\doubao\deskpet")
from PIL import Image, ImageChops

from pet import clean_edges

SRC = r"F:\AI产物\doubao\deskpet\assets\video_frames\sleep_full_cut"
DST = r"F:\AI产物\doubao\deskpet\assets\frames"

n = 0
for i in range(1, 124):
    src = os.path.join(SRC, f"n{i:03d}.png")
    if not os.path.exists(src):
        print("MISSING", src)
        continue
    im = Image.open(src).convert("RGBA")
    im = clean_edges(im)
    dst = os.path.join(DST, f"model_sleep_full_{i:03d}.png")
    im.save(dst)
    n += 1
print("processed", n)

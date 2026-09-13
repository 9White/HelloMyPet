# -*- coding: utf-8 -*-
"""伸懒腰 123 帧串行抠图：remove-image-background -> 下载 PNG。带限流退避与重试。"""
import json
import os
import re
import subprocess
import time

SRC = r"F:\AI产物\doubao\deskpet\assets\video_frames\user_stretch"
OUT = r"F:\AI产物\doubao\deskpet\assets\video_frames\user_stretch_cut"
os.makedirs(OUT, exist_ok=True)


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return r.stdout + r.stderr


def cut_one(i):
    jpg = os.path.join(SRC, "u%03d.jpg" % i)
    png = os.path.join(OUT, "u%03d.png" % i)
    if os.path.exists(png) and os.path.getsize(png) > 10000:
        return "skip"
    for attempt in range(3):
        out = run(["mediakit-cli", "image", "remove-image-background",
                   "--image-url", jpg, "--scene", "general",
                   "--output-format", "png"])
        m = re.search(r'"image_url": "([^"]+)"', out)
        if m:
            subprocess.run(["curl", "-s", "-L", "-o", png, m.group(1)],
                           check=False)
            if os.path.exists(png) and os.path.getsize(png) > 10000:
                return "ok"
        if attempt < 2:
            time.sleep(3)
    return "FAIL"


ok = fail = skip = 0
for i in range(1, 124):
    st = cut_one(i)
    if st == "ok":
        ok += 1
    elif st == "skip":
        skip += 1
    else:
        fail += 1
        print("fail", i, flush=True)
    if i % 25 == 0:
        print("progress", i, "ok", ok, "fail", fail, flush=True)
    time.sleep(0.5)
print("DONE ok", ok, "skip", skip, "fail", fail)

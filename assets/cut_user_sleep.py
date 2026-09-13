# -*- coding: utf-8 -*-
"""串行抠图用户睡觉 123 帧，限流重试"""
import json
import os
import subprocess
import time

SRC = r"F:\AI产物\doubao\deskpet\assets\video_frames\user_sleep"
OUT = r"F:\AI产物\doubao\deskpet\assets\video_frames\user_sleep_cut"
os.makedirs(OUT, exist_ok=True)

def cut_one(i, retry=6):
    p = os.path.join(OUT, f"u{i:03d}.png")
    if os.path.exists(p) and os.path.getsize(p) > 50000:
        return True
    src = os.path.join(SRC, f"u{i:03d}.jpg")
    for t in range(retry):
        r = subprocess.run(
            ["mediakit-cli", "image", "remove-image-background",
             "--image-url", src, "--scene", "general", "--output-format", "png"],
            capture_output=True, text=True, timeout=120)
        try:
            out = json.loads(r.stdout)
            if out.get("success"):
                u = out["image_url"]
                r2 = subprocess.run(["curl.exe", "-sL", "-o", p, u], capture_output=True, timeout=120)
                if os.path.exists(p) and os.path.getsize(p) > 50000:
                    return True
        except Exception:
            pass
        time.sleep(3 + t * 4)
    return False

fails = []
for i in range(1, 124):
    if cut_one(i):
        if i % 20 == 0:
            print(i, flush=True)
    else:
        fails.append(i)
        print("FAIL", i, flush=True)
    time.sleep(0.6)
print("done, fails:", fails)

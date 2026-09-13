# -*- coding: utf-8 -*-
"""侧躺帧抠图：串行 + 限流退避重试"""
import os
import re
import subprocess
import time

SRC = r"F:\AI产物\doubao\deskpet\assets\video_frames\user_side"
OUT = r"F:\AI产物\doubao\deskpet\assets\video_frames\user_side_cut"
os.makedirs(OUT, exist_ok=True)


def cut_one(i, retry=4):
    jpg = os.path.join(SRC, "u%03d.jpg" % i)
    png = os.path.join(OUT, "u%03d.png" % i)
    if os.path.exists(png) and os.path.getsize(png) > 10000:
        return True
    for t in range(retry):
        r = subprocess.run(["mediakit-cli", "image", "remove-image-background",
                            "--image-url", jpg, "--scene", "general",
                            "--output-format", "png"],
                           capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        m = re.search(r'"image_url": "([^"]+)"', r.stdout + r.stderr)
        if m:
            subprocess.run(["curl", "-s", "-L", "-o", png, m.group(1)], check=False)
            if os.path.exists(png) and os.path.getsize(png) > 10000:
                return True
        time.sleep(3 + t * 4)
    return False


missing = [i for i in range(1, 100)
           if not (os.path.exists(os.path.join(OUT, "u%03d.png" % i))
                   and os.path.getsize(os.path.join(OUT, "u%03d.png" % i)) > 10000)]
print("need cut:", len(missing), flush=True)
ok = 0
for n, i in enumerate(missing):
    if cut_one(i):
        ok += 1
    else:
        print("still fail", i, flush=True)
    if n % 10 == 9:
        print("progress", n + 1, "/", len(missing), flush=True)
    time.sleep(1)
print("DONE ok", ok, "/", len(missing))

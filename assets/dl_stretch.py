# -*- coding: utf-8 -*-
"""下载伸懒腰 123 帧原图到 assets/video_frames/user_stretch/"""
import os
import subprocess

OUT = r"F:\AI产物\doubao\deskpet\assets\video_frames\user_stretch"
os.makedirs(OUT, exist_ok=True)
urls = open(r"F:\AI产物\doubao\deskpet\assets\stretch_urls.txt",
            encoding="utf-8").read().splitlines()
print("total", len(urls))
for i, u in enumerate(urls, 1):
    p = os.path.join(OUT, "u%03d.jpg" % i)
    if os.path.exists(p) and os.path.getsize(p) > 5000:
        continue
    subprocess.run(["curl", "-s", "-L", "-o", p, u], check=False)
print("done")

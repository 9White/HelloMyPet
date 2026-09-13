# -*- coding: utf-8 -*-
"""下载侧躺帧"""
import os
import subprocess

URLS = r"F:\AI产物\doubao\deskpet\assets\side_urls.txt"
OUT = r"F:\AI产物\doubao\deskpet\assets\video_frames\user_side"
os.makedirs(OUT, exist_ok=True)

with open(URLS, encoding="utf-8") as f:
    urls = [l.strip() for l in f if l.strip()]

ok = 0
for i, u in enumerate(urls, 1):
    p = os.path.join(OUT, "u%03d.jpg" % i)
    if os.path.exists(p) and os.path.getsize(p) > 5000:
        ok += 1
        continue
    subprocess.run(["curl", "-s", "-L", "-o", p, u], check=False)
    if os.path.exists(p) and os.path.getsize(p) > 5000:
        ok += 1
print("downloaded", ok, "/", len(urls))

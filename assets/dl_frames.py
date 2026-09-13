# -*- coding: utf-8 -*-
"""解析抽帧结果，下载样本帧"""
import re
import subprocess
import os

raw = open(r"F:\AI产物\doubao\deskpet\assets\frames_out.json", encoding="utf-8").read()
urls = re.findall(r'"image_url": "([^"]+)"', raw)
print("total frames:", len(urls))
out = r"F:\AI产物\doubao\deskpet\assets"
for i, idx in enumerate([0, 1, 2, max(3, len(urls)//2), len(urls)-4, len(urls)-2, len(urls)-1]):
    u = urls[idx]
    subprocess.run(["curl", "-s", "-L", "-o",
                    os.path.join(out, "issue_f%d.jpg" % i), u], check=False)
print("downloaded")

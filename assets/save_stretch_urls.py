# -*- coding: utf-8 -*-
"""查询抽帧结果，保存帧 URL 列表"""
import re

raw = open(r"F:\AI产物\doubao\deskpet\assets\stretch_frames_out.json",
           encoding="utf-8").read()
urls = re.findall(r'"image_url": "([^"]+)"', raw)
print("frames:", len(urls))
with open(r"F:\AI产物\doubao\deskpet\assets\stretch_urls.txt", "w",
          encoding="utf-8") as f:
    f.write("\n".join(urls))

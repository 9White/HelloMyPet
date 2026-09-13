# -*- coding: utf-8 -*-
"""从任务 JSON 提取第二版 148 帧 URL 并下载"""
import json
import os
import urllib.request

TASK_JSON = r"F:\AI产物\doubao\deskpet\assets\video_frames\frames2_task.json"
OUT = r"F:\AI产物\doubao\deskpet\assets\video_frames\main_sleep2"
os.makedirs(OUT, exist_ok=True)

with open(TASK_JSON, encoding="utf-8") as f:
    text = f.read()
# 去掉 PowerShell 可能的 BOM/多余行，找到 JSON 起始
start = text.find("{")
data = json.loads(text[start:])
urls = [s["image_url"] for s in data["snapshots"]]
print("urls:", len(urls))
for i, url in enumerate(urls, 1):
    dest = os.path.join(OUT, f"f{i:03d}.jpg")
    if os.path.exists(dest) and os.path.getsize(dest) > 1000:
        continue
    try:
        urllib.request.urlretrieve(url, dest)
    except Exception as e:
        print(i, "FAIL", e)
    if i % 30 == 0:
        print(i, flush=True)
print("ALL DONE")

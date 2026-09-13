# -*- coding: utf-8 -*-
"""保存侧躺帧 URL 列表"""
import re
import subprocess

r = subprocess.run(["mediakit-cli", "shared", "query-task",
                    "--task-id", "amk-tool-extract-frames-884057701890"],
                   capture_output=True, text=True, encoding="utf-8", errors="replace")
out = r.stdout + r.stderr
urls = re.findall(r'"image_url": "(https://[^"]+)"', out)
print("total urls:", len(urls))
with open(r"F:\AI产物\doubao\deskpet\assets\side_urls.txt", "w", encoding="utf-8") as f:
    for u in urls:
        f.write(u + "\n")
print("saved")

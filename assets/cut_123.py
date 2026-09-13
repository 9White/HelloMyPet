# -*- coding: utf-8 -*-
"""123 帧串行抠图：mediakit-cli remove-image-background -> 下载透明 PNG"""
import json
import os
import subprocess
import sys
import time

SRC = r"F:\AI产物\doubao\deskpet\assets\video_frames\sleep_full"
OUT = r"F:\AI产物\doubao\deskpet\assets\video_frames\sleep_full_cut"
os.makedirs(OUT, exist_ok=True)

files = sorted(f for f in os.listdir(SRC) if f.lower().endswith(".jpg"))
print("total", len(files), flush=True)

ok, fail = 0, []
for idx, f in enumerate(files, 1):
    dst = os.path.join(OUT, f.replace(".jpg", ".png"))
    if os.path.exists(dst) and os.path.getsize(dst) > 1000:
        ok += 1
        continue
    src = os.path.join(SRC, f)
    for attempt in (1, 2):
        try:
            r = subprocess.run(
                ["mediakit-cli", "image", "remove-image-background",
                 "--image-url", src, "--scene", "general",
                 "--output-format", "png"],
                capture_output=True, text=True, timeout=180)
        except Exception as e:
            print(f"[{idx}/{len(files)}] {f} EXC {e}", flush=True)
            time.sleep(3)
            continue
        try:
            data = json.loads(r.stdout)
            url = data.get("image_url") or data.get("data", {}).get("image_url")
            if url:
                subprocess.run(["curl.exe", "-sL", "-o", dst, url],
                               check=True, timeout=120)
                if os.path.getsize(dst) > 1000:
                    ok += 1
                    print(f"[{idx}/{len(files)}] {f} OK", flush=True)
                    break
            err = data
        except Exception as e:
            print(f"[{idx}/{len(files)}] {f} PARSE {e} stderr={r.stderr[:200]}", flush=True)
        time.sleep(2)
    else:
        fail.append(f)
        print(f"[{idx}/{len(files)}] {f} FAIL", flush=True)

print("DONE ok=", ok, "fail=", fail, flush=True)

# -*- coding: utf-8 -*-
"""补齐 n097~n123 抠图：支持异步返回时 query-task 轮询"""
import json
import os
import subprocess
import time

SRC = r"F:\AI产物\doubao\deskpet\assets\video_frames\sleep_full"
OUT = r"F:\AI产物\doubao\deskpet\assets\video_frames\sleep_full_cut"
os.makedirs(OUT, exist_ok=True)

def run_cli(args):
    r = subprocess.run(args, capture_output=True, text=True, timeout=300)
    try:
        return json.loads(r.stdout)
    except Exception:
        return {"_raw": r.stdout[:500], "_err": r.stderr[:300]}

def download(url, dst):
    subprocess.run(["curl.exe", "-sL", "-o", dst, url], check=True, timeout=180)
    return os.path.exists(dst) and os.path.getsize(dst) > 1000

def process(i):
    src = os.path.join(SRC, f"n{i:03d}.jpg")
    dst = os.path.join(OUT, f"n{i:03d}.png")
    if os.path.exists(dst) and os.path.getsize(dst) > 1000:
        return True
    for attempt in range(1, 4):
        data = run_cli(["mediakit-cli", "image", "remove-image-background",
                        "--image-url", src, "--scene", "general",
                        "--output-format", "png"])
        url = data.get("image_url") or (data.get("data") or {}).get("image_url")
        if url:
            try:
                if download(url, dst):
                    return True
            except Exception as e:
                print(f"n{i:03d} dl err {e}", flush=True)
        tid = data.get("task_id")
        if tid and data.get("status") in ("running", "queued", None):
            q = run_cli(["mediakit-cli", "shared", "query-task",
                         "--task-id", tid, "--poll-complete"])
            url = q.get("image_url") or (q.get("data") or {}).get("image_url")
            if url and download(url, dst):
                return True
        time.sleep(4)
    return False

fail = []
for i in range(97, 124):
    ok = process(i)
    print(f"n{i:03d}", "OK" if ok else "FAIL", flush=True)
    if not ok:
        fail.append(i)
print("DONE fail=", fail, flush=True)

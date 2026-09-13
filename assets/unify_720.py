# -*- coding: utf-8 -*-
"""统一画幅：14 张主形象帧 675x900 -> 720x720 画布，主体底部对齐地面线 690，
使与 123 帧视频序列（已稳定化对齐 690）完全一致，切换动作不再有尺寸/位置跳变。
jump_air 腾空帧保持腾空高度（不落地）。"""
import os
import shutil
from PIL import Image

SRC = r"F:\AI产物\doubao\deskpet\assets\frames"
BAK = r"F:\AI产物\doubao\deskpet\assets\frames_bak_675x900"
os.makedirs(BAK, exist_ok=True)

NAMES = ["model_main", "model_doze", "model_side_stand", "model_walk_l",
         "model_walk_r", "model_stretch_arch", "model_stretch_reach",
         "model_stretch_flat", "model_look_l", "model_look_r",
         "model_lie_side", "model_sleep_curl", "model_jump_crouch",
         "model_jump_air"]

TARGET_BOTTOM = 690   # 地面线（与视频帧稳定化一致）
TARGET_CX = 383       # 水平中心（与视频帧稳定化一致）
CANVAS = 720

def try_H(H):
    results = {}
    for n in NAMES:
        p = os.path.join(SRC, n + ".png")
        im = Image.open(p).convert("RGBA")
        ratio = H / im.height
        w2 = round(im.width * ratio)
        im2 = im.resize((w2, H), Image.LANCZOS)
        a = im2.getchannel("A")
        m = a.point(lambda v: 255 if v >= 128 else 0)
        bb = m.getbbox()
        bb_orig = a.point(lambda v: 255 if v >= 128 else 0).getbbox()
        if n == "model_jump_air":
            # 腾空：底边离画布底的距离按原比例保留（原 900 画布 -> 720 画布）
            gap = (900 - bb_orig[3]) * CANVAS / 900
            y_air = CANVAS - gap          # 目标 bbox 底位置
            dy = y_air - bb[3]
        else:
            dy = TARGET_BOTTOM - bb[3]    # 底部对齐地面线
        dx = TARGET_CX - (bb[0] + bb[2]) // 2
        canvas = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
        canvas.paste(im2, (int(dx), int(dy)), im2)
        a2 = canvas.getchannel("A")
        b2 = a2.point(lambda v: 255 if v >= 128 else 0).getbbox()
        if b2 and (b2[0] < 0 or b2[1] < 0 or b2[2] > CANVAS or b2[3] > CANVAS):
            return None, f"{n} bbox out {b2}"
        results[n] = canvas
    return results, None

for H in (640, 620, 600, 580):
    results, err = try_H(H)
    if results:
        print("H =", H)
        for n, canvas in results.items():
            canvas.save(os.path.join(SRC, n + ".png"))
            b = canvas.getchannel("A").point(lambda v: 255 if v >= 128 else 0).getbbox()
            print(" ", n, "bbox", b, "size", canvas.size)
        print("OK")
        break
    print("H =", H, "failed:", err)
else:
    print("ALL H FAILED")

"""桌宠小猫 - 2.5D 建模形象（统一 720x720 画幅序列动画）

- 加载透明 PNG 精灵帧，统一缩放显示（全部帧同尺寸，切换无尺寸跳变）
- 动作 = 帧序列连续播放（走路 4 帧循环 / 伸懒腰 / 睡觉 123 帧 24fps 视频序列）
- 自然过渡：切换动作前闭眼，直接切帧，不做缩放放大
- 复用单个画布图像项换图，避免高频重绘闪烁
- 无边框、透明、置顶、可拖拽、右键菜单
"""
import os
import random
import tkinter as tk

from PIL import Image, ImageChops, ImageTk

TRANSPARENT = "#010203"
FRAMES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "frames")

DISPLAY_H = 320      # 统一显示高度（px，所有素材已统一 720x720 -> 320x320）
PAD = 0              # 窗口与图像完全同尺寸，无透明边（避免色键区域高频重绘闪烁）
BLINK_MS = 150       # 闭眼过渡时长（ms）
WALK_SPEED = 14      # 走路时窗口水平移动速度（px/帧）
WALK_DIST = 235      # 单程行走距离（px）

# 全部单帧素材文件（统一 2.5D 建模形象）
FRAME_FILES = {
    "main":   "model_main.png",          # 坐姿正面（形象设定图）
    "doze":   "model_doze.png",          # 闭眼端坐（眨眼/打盹/过渡闭眼）
    "side":   "model_side_stand.png",    # 侧身站立
    "walk_l": "model_walk_l.png",        # 走路：迈左前+右后
    "walk_r": "model_walk_r.png",        # 走路：迈右前+左后
    "stretch_arch":  "model_stretch_arch.png",   # 伸懒腰：低头弓背
    "stretch_reach": "model_stretch_reach.png",  # 伸懒腰：前爪前伸压低
    "stretch_flat":  "model_stretch_flat.png",   # 伸懒腰：完全展开
    "look_l": "model_look_l.png",        # 歪头向左
    "look_r": "model_look_r.png",        # 歪头向右
    "lie":    "model_lie_side.png",      # 侧躺
    "sleep_curl": "model_sleep_curl.png",  # 蜷睡
    "jump_crouch": "model_jump_crouch.png",  # 跳跃：蹲伏
    "jump_air":    "model_jump_air.png",     # 跳跃：腾空
}
# 视频动作序列帧（坐→蜷睡，来自真实动作视频，24fps 满帧率 123 帧）
for _i in range(1, 124):
    FRAME_FILES[f"sleep_full_{_i:03d}"] = f"model_sleep_full_{_i:03d}.png"

# 帧序列动作：连续动画（同一建模形象）
SEQUENCES = {
    "walk": {
        "frames": ["side", "walk_l", "side", "walk_r"],
        "loop": True, "frame_ms": 180, "total_ms": 6000,   # 走路循环 ~6 秒
    },
    "stretch": {
        "frames": ["main", "stretch_arch", "stretch_reach",
                   "stretch_flat", "main"],
        "loop": False, "frame_ms": 340, "total_ms": 0,
    },
    "look": {
        "frames": ["main", "look_l", "main", "look_r", "main"],
        "loop": False, "frame_ms": 360, "total_ms": 0,
    },
    "jump": {
        "frames": ["main", "jump_crouch", "jump_air", "side", "main"],
        "loop": False, "frame_ms": 280, "total_ms": 0,
    },
    "sleep_curl": {
        # 视频级"坐→蜷睡"序列：123 帧 @24fps 流畅播放，保持蜷睡后反向醒来
        "frames": [f"sleep_full_{_i:03d}" for _i in range(1, 124)],
        "loop": False, "frame_ms": 42, "total_ms": 0,
        "hold_last": 10000,        # 保持蜷睡 10 秒
        "reverse_on_exit": True,   # 醒来时反向播放（蜷→坐）
    },
}

# 随机动作表：(动作名, 单帧持续毫秒, 权重) —— 序列动作时长由 SEQUENCES 决定
ACTIONS = [
    ("doze",   4000, 20),
    ("stretch", 0, 17),
    ("look",     0, 16),
    ("walk",     0, 14),
    ("jump",     0, 12),
    ("lie",    5000, 11),
    ("sleep_curl", 9000, 10),
]
BLINK_WEIGHT = 30

# 动作过渡路径：进入某动作前，先依次展示的中间姿态（模拟真实动作衔接）
TRANSITION_PATHS = {
    "lie":        ["stretch_reach", "stretch_flat"],   # 坐 → 前伸 → 趴下 → 侧躺
}
# 离开某动作时的反向路径（慢慢回到坐姿）
REVERSE_PATHS = {
    "lie":        ["stretch_flat", "stretch_reach"],
}
TRANSITION_FRAME_MS = 340   # 过渡中间帧停留时长（ms）


def clean_edges(im):
    """清理透明图边缘残留，防止透明窗口上出现黑边/暗晕。

    原理：Windows 颜色键透明下，半透明像素会与近黑透明色混合而发暗。
    因此：1) 先清掉"半透明且偏暗"的残留（抠图黑边/阴影）；
         2) 其余半透明像素二值化——够实的毛边保留为全实，太淡的彻底透明。
    保留：完全不透明的暗色像素（猫真正的黑毛），不受影响。
    """
    r, g, b, a = im.split()
    # 1) 半透明且偏暗 -> 全透明（黑边、阴影、暗残留）
    sum_rgb = ImageChops.add(ImageChops.add(r, g), b)
    dark = sum_rgb.point(lambda v: 255 if v < 180 else 0)
    semi = a.point(lambda v: 255 if 0 < v < 245 else 0)
    a = ImageChops.subtract(a, ImageChops.multiply(dark, semi))
    # 2) 半透明像素二值化：alpha>=96 视为实体保留，否则完全透明
    a = a.point(lambda v: 255 if v >= 96 else 0)
    return Image.merge("RGBA", (r, g, b, a))


class PetWindow:
    def __init__(self, root):
        self.root = root
        self.state = "idle"        # idle / action / transition
        self._drag_offset = None

        root.overrideredirect(True)
        root.attributes("-topmost", True)
        root.attributes("-transparentcolor", TRANSPARENT)
        root.configure(bg=TRANSPARENT)

        self.canvas = tk.Canvas(root, bg=TRANSPARENT, highlightthickness=0)
        self.canvas.pack()
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<Button-3>", self._on_right_click)

        self._img_item = None    # 复用唯一画布图像项，避免 delete/create 造成闪烁

        self._load_frames()
        self._build_menu()
        self._resize_window("main", initial=True)
        self._display("main")

        self._schedule_next_action()

    # ---------------- 素材加载 ----------------
    def _load_frames(self):
        self.imgs = {}
        self.sizes = {}
        for name, fname in FRAME_FILES.items():
            path = os.path.join(FRAMES_DIR, fname)
            im = Image.open(path).convert("RGBA")
            im = clean_edges(im)
            w = round(im.width * DISPLAY_H / im.height)
            im = im.resize((w, DISPLAY_H), Image.LANCZOS)
            im = clean_edges(im)
            self.imgs[name] = ImageTk.PhotoImage(im)
            self.sizes[name] = (w, DISPLAY_H)

    # ---------------- 窗口与显示 ----------------
    def _size_of(self, name):
        """取某帧/某序列动作的显示尺寸"""
        if name in self.sizes:
            return self.sizes[name]
        if name in SEQUENCES:
            return self.sizes[SEQUENCES[name]["frames"][0]]
        return self.sizes["main"]

    def _resize_window(self, name, initial=False):
        w, h = self._size_of(name)
        cw, ch = w + PAD * 2, h + PAD * 2
        # 尺寸未变化时跳过 geometry，避免无谓的窗口重绘闪烁
        if (not initial and self.root.winfo_width() == cw
                and self.root.winfo_height() == ch):
            return
        self.canvas.config(width=cw, height=ch)
        if initial:
            sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
            x, y = sw - cw - 60, sh - ch - 80
        else:
            cur_w = self.root.winfo_width() or cw
            cur_h = self.root.winfo_height() or ch
            x = max(0, self.root.winfo_x() + (cur_w - cw))
            y = max(0, self.root.winfo_y() + (cur_h - ch))
        self.root.geometry(f"{cw}x{ch}+{x}+{y}")

    def _show_image(self, img, anchor, x, y):
        """复用同一个画布图像项换图，避免 delete+create 的闪烁"""
        if self._img_item is None:
            self._img_item = self.canvas.create_image(x, y, anchor=anchor, image=img)
        else:
            self.canvas.itemconfig(self._img_item, image=img, anchor=anchor)
            self.canvas.coords(self._img_item, x, y)

    def _display(self, name):
        self.frame_name = name
        self._show_image(self.imgs[name], "nw", PAD, PAD)

    def _center_show(self, name):
        w, h = self.sizes[name]
        cw, ch = w + PAD * 2, h + PAD * 2
        self._show_image(self.imgs[name], "center", cw // 2, ch // 2)

    # ---------------- 自然过渡 ----------------
    def _new_uid(self):
        """动作代际号：每次开始新动作递增，旧动作的过期回调据此丢弃"""
        self._act_uid = getattr(self, "_act_uid", 0) + 1
        return self._act_uid

    def _resolve_frame(self, name):
        """动作名 -> 实际显示帧名（序列动作取其起始帧）"""
        if name in SEQUENCES:
            return SEQUENCES[name]["frames"][0]
        return name

    def _transition_to(self, name, after_done=None):
        """动作切换：闭眼 -> 直接切到目标帧（不做缩放放大，动作衔接由帧内容完成）"""
        self.state = "transition"
        self._after_done = after_done
        uid = self._new_uid()
        self._resize_window(name)
        self._show_image(self.imgs["doze"], "nw", PAD, PAD)   # 闭眼
        self._trans_display = self._resolve_frame(name)
        self.root.after(BLINK_MS, lambda: self._finish_transition(uid))

    def _finish_transition(self, uid):
        if self.state != "transition" or uid != self._act_uid:
            return      # 防止过期回调
        self._display(self._trans_display)
        done, self._after_done = self._after_done, None
        if done:
            done()

    # ---------------- 待机：静态（不做上下浮动） ----------------

    # ---------------- 动作调度 ----------------
    def _schedule_next_action(self):
        self._action_job = self.root.after(
            random.randint(5000, 9000), self._run_random_action
        )

    def _run_random_action(self):
        if self.state != "idle":
            self._schedule_next_action()
            return
        if random.randint(0, 100) < BLINK_WEIGHT:
            self._do_blink()
        else:
            name, dur, _ = random.choices(
                ACTIONS, weights=[a[2] for a in ACTIONS]
            )[0]
            self._start_action(name, dur)

    def _do_blink(self):
        self.state = "transition"
        uid = self._new_uid()
        self._center_show("doze")
        self.root.after(BLINK_MS, lambda: self._end_blink(uid))

    def _end_blink(self, uid):
        if self.state != "transition" or uid != self._act_uid:
            return
        self._display("main")
        self.state = "idle"
        self._schedule_next_action()

    def _start_action(self, name, dur):
        if name in TRANSITION_PATHS:
            # 先走"动作过渡链"：伸展→趴下→… 再进入目标动作
            self._play_transition_path(
                TRANSITION_PATHS[name],
                lambda: self._enter_action(name, dur),
            )
        else:
            self._enter_action(name, dur)

    def _enter_action(self, name, dur):
        self._last_action_name = name
        if name in SEQUENCES:
            self._transition_to(name, after_done=lambda: self._play_sequence(name))
        else:
            self._transition_to(name, after_done=lambda: self._hold_single(name, dur))

    def _play_transition_path(self, frames, on_done):
        """依次展示中间姿态帧，播完回调 on_done"""
        self.state = "transition"
        self._path = {"frames": frames, "idx": 0, "on_done": on_done,
                      "uid": self._new_uid()}
        self._path_step()

    def _path_step(self):
        p = self._path
        if not p or p.get("uid") != self._act_uid:
            return
        self._display(p["frames"][p["idx"]])
        p["idx"] += 1
        if p["idx"] >= len(p["frames"]):
            self._path = None
            p["on_done"]()
            return
        self.root.after(TRANSITION_FRAME_MS, self._path_step)

    def _hold_single(self, name, dur):
        self.state = "action"
        uid = self._new_uid()
        self.root.after(dur, lambda: self._end_action_checked(uid))

    def _end_action_checked(self, uid):
        if self.state != "action" or uid != self._act_uid:
            return
        self._end_action()

    # ---- 序列动画 ----
    def _play_sequence(self, name):
        seq = SEQUENCES[name]
        self.state = "action"
        self._seq = {
            "name": name, "idx": 0, "reverse": False,
            "frames": seq["frames"], "loop": seq["loop"],
            "frame_ms": seq["frame_ms"],
            "elapsed": 0, "total": seq["total_ms"],
            "hold_last": seq.get("hold_last", 0),
            "uid": self._new_uid(),
        }
        if name == "walk":
            self._walk_dir = 1
            self._walk_done = 0      # 已走完的单程段数
        self._seq_step()

    def _seq_step(self):
        s = self._seq
        if not s or s.get("uid") != self._act_uid:
            return      # 过期序列回调（已被新动作取代）直接终止
        frames = s["frames"]
        self._display(frames[s["idx"]])
        if s["name"] == "walk":
            self._walk_move()
        s["idx"] += -1 if s["reverse"] else 1
        s["elapsed"] += s["frame_ms"]

        if s["reverse"]:
            if s["idx"] < 0:
                self._seq = None
                self._transition_to("main", after_done=self._back_idle)
                return
        elif s["idx"] >= len(frames):
            if s["loop"] and (not s["total"] or s["elapsed"] < s["total"]):
                s["idx"] = 0
            else:
                seq_end = s
                self._seq = None
                if seq_end["hold_last"]:
                    # 保持最后一帧，之后进入退出流程
                    self._hold_last_job = self.root.after(
                        seq_end["hold_last"], self._exit_sequence, seq_end
                    )
                else:
                    self._end_action()
                return
        self.root.after(s["frame_ms"], self._seq_step)

    def _exit_sequence(self, s):
        """序列动作结束：支持反向播放退出（如睡觉醒来）"""
        if self.state != "action" or s.get("uid") != self._act_uid:
            return
        if s.get("reverse_on_exit"):
            self._seq = {
                "name": s["name"], "idx": len(s["frames"]) - 1, "reverse": True,
                "frames": s["frames"], "loop": False,
                "frame_ms": s["frame_ms"],
                "elapsed": 0, "total": 0, "hold_last": 0,
                "uid": self._new_uid(),
            }
            self._seq_step()
        else:
            self._end_action()

    def _walk_move(self):
        """走路时窗口水平移动；到边界或走完往返则反向/结束"""
        x = self.root.winfo_x() + self._walk_dir * WALK_SPEED
        cw = self.root.winfo_width()
        sw = self.root.winfo_screenwidth()
        x = max(0, min(x, sw - cw))
        self.root.geometry(f"+{x}+{self.root.winfo_y()}")
        if x <= 0 or x >= sw - cw:
            self._walk_dir *= -1
            self._walk_done += 1

    def _end_action(self):
        if self.state != "action":
            return      # 防止过期回调打断新动作
        rev = REVERSE_PATHS.get(self._last_action_name, [])
        if rev:
            # 先反向过渡（蜷→趴→伸展）再回坐姿
            self._play_transition_path(
                rev, lambda: self._transition_to("main", after_done=self._back_idle)
            )
        else:
            self._transition_to("main", after_done=self._back_idle)

    def _back_idle(self):
        self.state = "idle"
        self._schedule_next_action()

    # ---- 坐着（原地眨眼） ----
    def _start_sit(self):
        self._transition_to("main", after_done=self._sit_loop)

    def _sit_loop(self):
        self.state = "action"
        self._sit_blink_cycle()

    def _sit_blink_cycle(self):
        """睁眼坐姿，随机 1.2~2.6 秒后眨眼"""
        if self.state != "action":
            return
        self._display("main")
        self.root.after(random.randint(1200, 2600), self._sit_blink_close)

    def _sit_blink_close(self):
        if self.state != "action":
            return
        self._display("doze")          # 闭眼
        self.root.after(170, self._sit_blink_cycle)

    # ---------------- 右键菜单 ----------------
    def _build_menu(self):
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="桌宠小猫（2.5D 建模版）", state="disabled")
        menu.add_separator()
        menu.add_command(label="坐着", command=self._start_sit)
        menu.add_command(label="散步", command=lambda: self._start_action("walk", 0))
        menu.add_command(label="伸懒腰", command=lambda: self._start_action("stretch", 0))
        menu.add_command(label="跳一下", command=lambda: self._start_action("jump", 0))
        menu.add_command(label="睡觉", command=lambda: self._start_action("sleep_curl", 100000))
        menu.add_command(label="退出", command=self.root.destroy)
        self.menu = menu

    # ---------------- 事件 ----------------
    def _on_press(self, event):
        self._drag_offset = (
            event.x_root - self.root.winfo_x(),
            event.y_root - self.root.winfo_y(),
        )

    def _on_drag(self, event):
        if self._drag_offset:
            x = event.x_root - self._drag_offset[0]
            y = event.y_root - self._drag_offset[1]
            self.root.geometry(f"+{x}+{y}")

    def _on_right_click(self, event):
        self.menu.tk_popup(event.x_root, event.y_root)

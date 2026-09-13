"""桌宠小猫 - Qt 版（真透明渲染，无闪烁）

- PyQt6 透明窗口（per-pixel alpha + 双缓冲），换帧不闪
- 复用统一 720x720 素材与动画逻辑：动作序列 / 自然过渡 / 随机动作 / 防竞态
- 无边框、真透明、置顶、可拖拽、右键菜单
"""
import ctypes
import os
import random
import sys
from ctypes import wintypes

from PIL import Image, ImageChops
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QIcon, QImage, QPainter, QPixmap
from PyQt6.QtWidgets import (QApplication, QMenu, QSystemTrayIcon, QWidget)

FRAMES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "frames")
TRAY_ICON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "tray_icon.png")

FS_CHECK_MS = 500    # 全屏检测轮询间隔（ms）
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
AUTOSTART_NAME = "DeskPetCat"


def _is_fullscreen_on_screen(pet_hwnd):
    """前台窗口是否完全覆盖桌宠所在显示器（视频/游戏/演示全屏）"""
    try:
        user32 = ctypes.windll.user32
        fg = user32.GetForegroundWindow()
        if not fg or fg == pet_hwnd:
            return False
        # 排除桌面窗口（点击桌面空白处会激活全屏桌面子窗口）
        if fg == user32.GetShellWindow():
            return False
        cls = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(fg, cls, 256)
        if cls.value in ("Progman", "WorkerW"):
            return False
        mon = user32.MonitorFromWindow(pet_hwnd, 2)  # MONITOR_DEFAULTTONEAREST

        class MONITORINFO(ctypes.Structure):
            _fields_ = [("cbSize", wintypes.DWORD),
                        ("rcMonitor", wintypes.RECT),
                        ("rcWork", wintypes.RECT),
                        ("dwFlags", wintypes.DWORD)]

        mi = MONITORINFO()
        mi.cbSize = ctypes.sizeof(MONITORINFO)
        if not user32.GetMonitorInfoW(mon, ctypes.byref(mi)):
            return False
        scr = mi.rcMonitor
        r = wintypes.RECT()
        if not user32.GetWindowRect(fg, ctypes.byref(r)):
            return False
        tol = 4
        return (r.left <= scr.left + tol and r.top <= scr.top + tol
                and r.right >= scr.right - tol and r.bottom >= scr.bottom - tol)
    except Exception:
        return False

DISPLAY_H = 320      # 统一显示高度（px，全部素材 720x720 -> 320x320）
BLINK_MS = 150       # 闭眼过渡时长（ms）
WALK_SPEED = 14      # 走路时窗口水平移动速度（px/帧）
WALK_DIST = 235      # 单程行走距离（px）

# 全部单帧素材文件（统一 2.5D 建模形象）
FRAME_FILES = {
    "main":   "model_main.png",
    "doze":   "model_doze.png",
    "side":   "model_side_stand.png",
    "walk_l": "model_walk_l.png",
    "walk_r": "model_walk_r.png",
    "stretch_arch":  "model_stretch_arch.png",
    "stretch_reach": "model_stretch_reach.png",
    "stretch_flat":  "model_stretch_flat.png",
    "look_l": "model_look_l.png",
    "look_r": "model_look_r.png",
    "lie":    "model_lie_side.png",
    "sleep_curl": "model_sleep_curl.png",
    "jump_crouch": "model_jump_crouch.png",
    "jump_air":    "model_jump_air.png",
}
for _i in range(1, 124):
    FRAME_FILES[f"sleep_full_{_i:03d}"] = f"model_sleep_full_{_i:03d}.png"
for _i in range(1, 124):
    FRAME_FILES[f"stretch_full_{_i:03d}"] = f"model_stretch_full_{_i:03d}.png"

SEQUENCES = {
    "walk": {
        "frames": ["side", "walk_l", "side", "walk_r"],
        "loop": True, "frame_ms": 180, "total_ms": 6000,
    },
    "stretch": {
        "frames": [f"stretch_full_{_i:03d}" for _i in range(1, 124)],
        "loop": False, "frame_ms": 42, "total_ms": 0,
        "hold_last": 500, "reverse_on_exit": True,
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
        "frames": [f"sleep_full_{_i:03d}" for _i in range(1, 124)],
        "loop": False, "frame_ms": 42, "total_ms": 0,
        "hold_last": 10000,
        "reverse_on_exit": True,
    },
}

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

TRANSITION_PATHS = {
    "lie": ["stretch_reach", "stretch_flat"],
}
REVERSE_PATHS = {
    "lie": ["stretch_flat", "stretch_reach"],
}
TRANSITION_FRAME_MS = 340


def clean_edges(im):
    """清理透明图边缘残留（黑边/暗晕），温和处理，保留羽化渐变"""
    r, g, b, a = im.split()
    sum_rgb = ImageChops.add(ImageChops.add(r, g), b)
    dark = sum_rgb.point(lambda v: 255 if v < 300 else 0)
    semi = a.point(lambda v: 255 if 0 < v < 245 else 0)
    a = ImageChops.subtract(a, ImageChops.multiply(dark, semi))
    return Image.merge("RGBA", (r, g, b, a))


def premultiply(im):
    """alpha 预乘（避免缩放时边缘与透明黑混合产生暗边）"""
    r, g, b, a = im.split()
    return Image.merge("RGBA", (ImageChops.multiply(r, a),
                                ImageChops.multiply(g, a),
                                ImageChops.multiply(b, a), a))


def unpremultiply(im):
    """反预乘：只处理半透明像素（数量少，速度快）"""
    r, g, b, a = im.split()
    pr, pg, pb, pa = (list(x.getdata()) for x in (r, g, b, a))
    for i, (R, G, B, A) in enumerate(zip(pr, pg, pb, pa)):
        if 0 < A < 255:
            pr[i] = min(255, R * 255 // A)
            pg[i] = min(255, G * 255 // A)
            pb[i] = min(255, B * 255 // A)
    r.putdata(pr)
    g.putdata(pg)
    b.putdata(pb)
    return Image.merge("RGBA", (r, g, b, a))


def pil_to_qpixmap(im):
    im = im.convert("RGBA")
    data = im.tobytes("raw", "RGBA")
    qimg = QImage(data, im.width, im.height, im.width * 4,
                  QImage.Format.Format_RGBA8888).copy()
    return QPixmap.fromImage(qimg)


class PetWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.state = "idle"
        self._drag_offset = None

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self._cur_pixmap = None
        self._fs_hidden = False
        self._manual_hidden = False
        self._sit_uid = 0

        self._load_frames()
        self._build_menu()
        self._resize_window("main", initial=True)
        self._display("main")
        self._schedule_next_action()
        self._build_tray()

        self._fs_timer = QTimer(self)
        self._fs_timer.timeout.connect(self._check_fullscreen)
        self._fs_timer.start(FS_CHECK_MS)

    # ---------------- 系统托盘 ----------------
    def _build_tray(self):
        self.tray = QSystemTrayIcon(QIcon(TRAY_ICON), self)
        self.tray.setToolTip("桌宠小猫")
        menu = QMenu()
        self.act_show = menu.addAction("隐藏小猫", self.toggle_visible)
        menu.addSeparator()
        self.act_autostart = menu.addAction("开机自启动")
        self.act_autostart.setCheckable(True)
        self.act_autostart.setChecked(self.is_autostart_enabled())
        self.act_autostart.toggled.connect(self.set_autostart)
        menu.addSeparator()
        menu.addAction("退出", self.close)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

    def _on_tray_activated(self, reason):
        if reason in (QSystemTrayIcon.ActivationReason.Trigger,
                      QSystemTrayIcon.ActivationReason.DoubleClick):
            self.toggle_visible()

    def toggle_visible(self):
        if self.isVisible():
            self._manual_hidden = True
            self.hide()
            self.act_show.setText("显示小猫")
        else:
            self._manual_hidden = False
            self._fs_hidden = False
            self.show()
            self.act_show.setText("隐藏小猫")

    # ---------------- 开机自启动 ----------------
    @staticmethod
    def _autostart_cmd():
        py = sys.executable
        pyw = os.path.join(os.path.dirname(py), "pythonw.exe")
        if not os.path.exists(pyw):
            pyw = py
        entry = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")
        return f'"{pyw}" "{entry}"'

    @staticmethod
    def is_autostart_enabled():
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:
                winreg.QueryValueEx(k, AUTOSTART_NAME)
                return True
        except FileNotFoundError:
            return False

    def set_autostart(self, on):
        import winreg
        try:
            if on:
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:
                    winreg.SetValueEx(k, AUTOSTART_NAME, 0,
                                      winreg.REG_SZ, self._autostart_cmd())
            else:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0,
                                    winreg.KEY_SET_VALUE) as k:
                    winreg.DeleteValue(k, AUTOSTART_NAME)
        except OSError:
            self.act_autostart.blockSignals(True)
            self.act_autostart.setChecked(not on)
            self.act_autostart.blockSignals(False)

    # ---------------- 全屏隐藏 ----------------
    def _check_fullscreen(self):
        if self._manual_hidden:
            return
        try:
            fs = _is_fullscreen_on_screen(int(self.winId()))
        except Exception:
            return
        if fs and not self._fs_hidden:
            self._fs_hidden = True
            self.hide()
        elif not fs and self._fs_hidden:
            self._fs_hidden = False
            self.show()

    # ---------------- 素材加载 ----------------
    def _load_frames(self):
        self.pixmaps = {}
        self.sizes = {}
        for name, fname in FRAME_FILES.items():
            path = os.path.join(FRAMES_DIR, fname)
            im = Image.open(path).convert("RGBA")
            im = clean_edges(im)
            w = round(im.width * DISPLAY_H / im.height)
            # 预乘后缩放（预乘域插值，避免边缘与透明黑混合产生暗边），
            # 再反预乘并硬切半透明过渡带：轮廓=实心毛色，任何底色下无黑边/虚线/白边
            im = premultiply(im).resize((w, DISPLAY_H), Image.LANCZOS)
            im = unpremultiply(im)
            r, g, b, a = im.split()
            a = a.point(lambda v: 255 if v >= 240 else 0)
            im = Image.merge("RGBA", (r, g, b, a))
            self.pixmaps[name] = pil_to_qpixmap(im)
            self.sizes[name] = (w, DISPLAY_H)

    # ---------------- 窗口与显示 ----------------
    def _size_of(self, name):
        if name in self.sizes:
            return self.sizes[name]
        if name in SEQUENCES:
            return self.sizes[SEQUENCES[name]["frames"][0]]
        return self.sizes["main"]

    def _resize_window(self, name, initial=False):
        w, h = self._size_of(name)
        if not initial and self.width() == w and self.height() == h:
            return
        self.setFixedSize(w, h)
        if initial:
            scr = QApplication.primaryScreen().availableGeometry()
            x = scr.width() - w - 60
            y = scr.height() - h - 80
            self.move(x, y)
        else:
            # 保持右下角锚定
            right = self.x() + self.width()
            bottom = self.y() + self.height()
            self.setFixedSize(w, h)
            self.move(right - w, bottom - h)

    def _display(self, name):
        self.frame_name = name
        self._cur_pixmap = self.pixmaps[name]
        self.update()            # 请求重绘（Qt 双缓冲，平滑无闪烁）

    def paintEvent(self, e):
        if self._cur_pixmap is None:
            return
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self._cur_pixmap)
        painter.end()

    # ---------------- 自然过渡 ----------------
    def _new_uid(self):
        self._act_uid = getattr(self, "_act_uid", 0) + 1
        return self._act_uid

    def _resolve_frame(self, name):
        if name in SEQUENCES:
            return SEQUENCES[name]["frames"][0]
        return name

    def _transition_to(self, name, after_done=None):
        self.state = "transition"
        self._after_done = after_done
        uid = self._new_uid()
        self._resize_window(name)
        self._display("doze")
        self._trans_display = self._resolve_frame(name)
        QTimer.singleShot(BLINK_MS, lambda: self._finish_transition(uid))

    def _finish_transition(self, uid):
        if self.state != "transition" or uid != self._act_uid:
            return
        self._display(self._trans_display)
        done, self._after_done = self._after_done, None
        if done:
            done()

    # ---------------- 动作调度 ----------------
    def _schedule_next_action(self):
        QTimer.singleShot(random.randint(5000, 9000), self._run_random_action)

    def _run_random_action(self):
        if self.state != "idle":
            self._schedule_next_action()
            return
        if random.randint(0, 100) < BLINK_WEIGHT:
            self._do_blink()
        else:
            name, dur, _ = random.choices(
                ACTIONS, weights=[a[2] for a in ACTIONS])[0]
            self._start_action(name, dur)

    def _do_blink(self):
        self.state = "transition"
        uid = self._new_uid()
        self._display("doze")
        QTimer.singleShot(BLINK_MS, lambda: self._end_blink(uid))

    def _end_blink(self, uid):
        if self.state != "transition" or uid != self._act_uid:
            return
        self._display("main")
        self.state = "idle"
        self._schedule_next_action()

    def _start_action(self, name, dur):
        if name in TRANSITION_PATHS:
            self._play_transition_path(
                TRANSITION_PATHS[name],
                lambda: self._enter_action(name, dur))
        else:
            self._enter_action(name, dur)

    def _enter_action(self, name, dur):
        self._last_action_name = name
        if name in SEQUENCES:
            self._transition_to(name, after_done=lambda: self._play_sequence(name, dur))
        else:
            self._transition_to(name, after_done=lambda: self._hold_single(name, dur))

    def _play_transition_path(self, frames, on_done):
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
        QTimer.singleShot(TRANSITION_FRAME_MS, self._path_step)

    def _hold_single(self, name, dur):
        self.state = "action"
        uid = self._new_uid()
        QTimer.singleShot(dur, lambda: self._end_action_checked(uid))

    def _end_action_checked(self, uid):
        if self.state != "action" or uid != self._act_uid:
            return
        self._end_action()

    # ---- 序列动画 ----
    def _play_sequence(self, name, dur=None):
        seq = SEQUENCES[name]
        self.state = "action"
        self._seq = {
            "name": name, "idx": 0, "reverse": False,
            "frames": seq["frames"], "loop": seq["loop"],
            "frame_ms": seq["frame_ms"],
            "elapsed": 0, "total": seq["total_ms"],
            "hold_last": dur if dur else seq.get("hold_last", 0),
            "reverse_on_exit": seq.get("reverse_on_exit", False),
            "uid": self._new_uid(),
        }
        if name == "walk":
            self._walk_dir = 1
            self._walk_done = 0
        self._seq_step()

    def _seq_step(self):
        s = self._seq
        if not s or s.get("uid") != self._act_uid:
            return
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
                    QTimer.singleShot(seq_end["hold_last"],
                                      lambda: self._exit_sequence(seq_end))
                else:
                    self._end_action()
                return
        QTimer.singleShot(s["frame_ms"], self._seq_step)

    def _exit_sequence(self, s):
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
        x = self.x() + self._walk_dir * WALK_SPEED
        sw = QApplication.primaryScreen().availableGeometry().width()
        x = max(0, min(x, sw - self.width()))
        self.move(x, self.y())
        if x <= 0 or x >= sw - self.width():
            self._walk_dir *= -1
            self._walk_done += 1

    def _end_action(self):
        if self.state != "action":
            return
        rev = REVERSE_PATHS.get(self._last_action_name, [])
        if rev:
            self._play_transition_path(
                rev, lambda: self._transition_to("main", after_done=self._back_idle))
        else:
            self._transition_to("main", after_done=self._back_idle)

    def _back_idle(self):
        self.state = "idle"
        self._schedule_next_action()

    # ---- 坐着（原地眨眼） ----
    def _start_sit(self):
        self._sit_uid = self._new_uid()
        self._transition_to("main", after_done=self._sit_loop)

    def _sit_loop(self):
        self.state = "action"
        self._sit_blink_cycle()

    def _sit_blink_cycle(self):
        if self.state != "action" or self._sit_uid != self._act_uid:
            return
        self._display("main")
        QTimer.singleShot(random.randint(1200, 2600), self._sit_blink_close)

    def _sit_blink_close(self):
        if self.state != "action" or self._sit_uid != self._act_uid:
            return
        self._display("doze")
        QTimer.singleShot(170, self._sit_blink_cycle)

    # ---------------- 右键菜单 ----------------
    def _build_menu(self):
        menu = QMenu(self)
        act = QAction("桌宠小猫（2.5D 建模版）", self)
        act.setEnabled(False)
        menu.addAction(act)
        menu.addSeparator()
        menu.addAction("坐着", self._start_sit)
        menu.addAction("散步", lambda: self._start_action("walk", 0))
        menu.addAction("伸懒腰", lambda: self._start_action("stretch", 0))
        menu.addAction("跳一下", lambda: self._start_action("jump", 0))
        menu.addAction("睡觉", lambda: self._start_action(
            "sleep_curl", random.randint(30 * 60 * 1000, 120 * 60 * 1000)))
        menu.addAction("退出", self.close)
        self.menu = menu

    # ---------------- 事件 ----------------
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = (e.globalPosition().toPoint()
                                 - self.frameGeometry().topLeft())

    def mouseMoveEvent(self, e):
        if self._drag_offset is not None:
            self.move(e.globalPosition().toPoint() - self._drag_offset)

    def mouseReleaseEvent(self, e):
        self._drag_offset = None

    def contextMenuEvent(self, e):
        self.menu.exec(e.globalPos())

    def closeEvent(self, e):
        QApplication.instance().quit()

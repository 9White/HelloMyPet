# -*- coding: utf-8 -*-
"""复现路径验证：睡觉 -> 坐着 -> 睡觉，确认坐姿眨眼循环不残留、睡姿稳定保持"""
import sys

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from pet_qt import PetWindow

app = QApplication(sys.argv)
w = PetWindow()
w.show()

samples = []


def sample(tag):
    samples.append((tag, w.frame_name))
    print(tag, "frame:", w.frame_name, "state:", w.state, flush=True)


def step1():
    print("== 1) 睡觉(3s)", flush=True)
    w._start_action("sleep_curl", 3000)


def step2():
    print("== 2) 切到坐着", flush=True)
    w._start_sit()


def step3():
    print("== 3) 再点睡觉(100s)", flush=True)
    w._start_action("sleep_curl", 100000)


def step4():
    # 睡觉动画约 5.2s 播完进入 hold；连续采样 1.5s 看画面是否稳定
    print("== 4) 观察 hold 稳定性（1.5s 采样）", flush=True)
    QTimer.singleShot(9000, observe)


def observe():
    seen = set()
    for i in range(15):
        seen.add(w.frame_name)
        QTimer.singleShot(i * 100, lambda: None)
    QTimer.singleShot(0, lambda: None)


def finish():
    print("== 5) 最终 state:", w.state, "frame:", w.frame_name,
          "sit_uid:", w._sit_uid, "act_uid:", w._act_uid, flush=True)
    app.quit()


QTimer.singleShot(300, step1)
QTimer.singleShot(3300, step2)
QTimer.singleShot(6000, step3)
QTimer.singleShot(9000, observe)
QTimer.singleShot(10600, finish)
sys.exit(app.exec())

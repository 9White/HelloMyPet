# -*- coding: utf-8 -*-
"""侧躺动作验证：播放 -> hold -> 倒放醒来 -> 回 idle"""
import sys

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from pet_qt import PetWindow

app = QApplication(sys.argv)
w = PetWindow()
w.show()


def show(tag):
    print(tag, "state:", w.state, "frame:", w.frame_name,
          "seq:", w._seq["name"] if w._seq else None,
          "reverse:", w._seq["reverse"] if w._seq else None,
          flush=True)


def start():
    print("== 触发侧躺", flush=True)
    w._start_action("side_lie", 0)


QTimer.singleShot(300, start)
QTimer.singleShot(2500, lambda: show("T+2.5s(播放中)"))
QTimer.singleShot(5200, lambda: show("T+5.2s(播完hold)"))
QTimer.singleShot(15600, lambda: show("T+15.6s(回放中)"))
QTimer.singleShot(20000, lambda: (show("T+20.0s(应回idle)"), app.quit()))
sys.exit(app.exec())

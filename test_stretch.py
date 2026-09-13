# -*- coding: utf-8 -*-
"""伸懒腰动作验证：播放 -> hold -> 回放收回 -> 回 idle"""
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
    print("== 触发伸懒腰", flush=True)
    w._start_action("stretch", 0)


QTimer.singleShot(300, start)
QTimer.singleShot(2500, lambda: show("T+2.5s(播放中)"))
QTimer.singleShot(5600, lambda: show("T+5.6s(播完hold)"))
QTimer.singleShot(7000, lambda: show("T+7.0s(回放中)"))
QTimer.singleShot(11500, lambda: (show("T+11.5s(应回idle)"), app.quit()))
sys.exit(app.exec())

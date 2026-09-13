# -*- coding: utf-8 -*-
"""睡觉保持逻辑验证：触发 100 秒睡觉，8/15 秒后检查是否还在睡"""
import sys

from PyQt6.QtWidgets import QApplication

from pet_qt import PetWindow

app = QApplication(sys.argv)
w = PetWindow()
w.show()

# 触发 100 秒睡觉（正常菜单传 30-120 分钟，这里用 100 秒快速验证保持逻辑）
w._start_action("sleep_curl", 100000)
print("T0 start sleep, state:", w.state, flush=True)


def check(tag):
    print(tag, "state:", w.state,
          "seq:", w._seq["name"] if w._seq else None,
          "hold_last:", w._seq["hold_last"] if w._seq else None,
          flush=True)


# 播放约 5.2 秒后进入 hold，8 秒 / 15 秒检查
from PyQt6.QtCore import QTimer

QTimer.singleShot(8000, lambda: check("T+8s "))
QTimer.singleShot(15000, lambda: (check("T+15s"), app.quit()))
sys.exit(app.exec())

"""桌宠小猫 - 启动入口（Qt 真透明渲染版）"""
import ctypes
import sys

from PyQt6.QtWidgets import QApplication

from pet_qt import PetWindow

MUTEX_NAME = "DeskPetCat_SingleInstance"


def _ensure_single_instance():
    """防止多实例：已有桌宠运行则直接退出"""
    kernel32 = ctypes.windll.kernel32
    kernel32.CreateMutexW(None, False, MUTEX_NAME)
    if kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
        return False
    return True


def main():
    if not _ensure_single_instance():
        print("桌宠已在运行")
        return
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # 托盘常驻：隐藏窗口不退出
    w = PetWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

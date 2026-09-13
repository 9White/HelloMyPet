# -*- coding: utf-8 -*-
"""启用桌宠开机自启动（注册表 Run 键，与托盘菜单同一逻辑）"""
import os
import sys
import winreg

py = sys.executable
pyw = os.path.join(os.path.dirname(py), "pythonw.exe")
if not os.path.exists(pyw):
    pyw = py
entry = r"F:\AI产物\doubao\deskpet\main.py"
cmd = '"{}" "{}"'.format(pyw, entry)
key = winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                       r"Software\Microsoft\Windows\CurrentVersion\Run")
winreg.SetValueEx(key, "DeskPetCat", 0, winreg.REG_SZ, cmd)
winreg.CloseKey(key)

k = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                   r"Software\Microsoft\Windows\CurrentVersion\Run")
v, _ = winreg.QueryValueEx(k, "DeskPetCat")
winreg.CloseKey(k)
print("autostart set:", v)

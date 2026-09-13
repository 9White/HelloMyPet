# -*- coding: utf-8 -*-
"""以 UTF-8 BOM 写 PowerShell 脚本并执行，创建中文名快捷方式（避免 GBK 乱码）"""
import os
import subprocess

PS1 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "make_shortcut.ps1")
PYW = r"C:\Users\smile\AppData\Local\Doubao\User Data\sandbox_runtime\bases\c98c5042338ed152c6f10ecd8591889f\python\pythonw.exe"
ENTRY = r"F:\AI产物\doubao\deskpet\main.py"
ICON = r"F:\AI产物\doubao\deskpet\assets\tray_icon.ico"

content = """$startMenu = [Environment]::GetFolderPath('Programs')
$lnk = Join-Path $startMenu '桌宠小猫.lnk'
$ws = New-Object -ComObject WScript.Shell
$sc = $ws.CreateShortcut($lnk)
$sc.TargetPath = '%s'
$sc.Arguments = '"%s"'
$sc.WorkingDirectory = 'F:\\AI产物\\doubao\\deskpet'
$sc.IconLocation = '%s,0'
$sc.Description = '桌宠小猫'
$sc.Save()
Write-Output ('lnk created: ' + $lnk)
""" % (PYW, ENTRY, ICON)

with open(PS1, "w", encoding="utf-8-sig") as f:
    f.write(content)

r = subprocess.run(
    ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", PS1],
    capture_output=True, text=True, encoding="utf-8", errors="replace")
print(r.stdout)
print(r.stderr)

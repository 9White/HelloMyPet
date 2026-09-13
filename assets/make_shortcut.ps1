$startMenu = [Environment]::GetFolderPath('Programs')
$lnk = Join-Path $startMenu '桌宠小猫.lnk'
$ws = New-Object -ComObject WScript.Shell
$sc = $ws.CreateShortcut($lnk)
$sc.TargetPath = 'C:\Users\smile\AppData\Local\Doubao\User Data\sandbox_runtime\bases\c98c5042338ed152c6f10ecd8591889f\python\pythonw.exe'
$sc.Arguments = '"F:\AI产物\doubao\deskpet\main.py"'
$sc.WorkingDirectory = 'F:\AI产物\doubao\deskpet'
$sc.IconLocation = 'F:\AI产物\doubao\deskpet\assets\tray_icon.ico,0'
$sc.Description = '桌宠小猫'
$sc.Save()
Write-Output ('lnk created: ' + $lnk)

﻿# SmartHome - Launch backend and frontend in separate terminal windows.
# Each window runs independently - closing one does not affect the other.

# === Backend Terminal ===
Start-Process powershell -ArgumentList @(
    '-NoExit',
    '-Command',
    'Set-Location "d:\111_daxueshengshilizongjie\SmartHome\test\zys-dev\src\smarthome\python"; python start_services.py'
) -WindowStyle Normal

# === Frontend Terminal ===
Start-Process powershell -ArgumentList @(
    '-NoExit',
    '-Command',
    'Set-Location "d:\111_daxueshengshilizongjie\SmartHome\test\zys-dev\src\smarthome\web"; npm run dev:h5'
) -WindowStyle Normal
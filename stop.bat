@echo off
powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"name='python.exe'\" | Where-Object { $_.CommandLine -like '*focustrack*main.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"
echo FocusTrack stopped (if it was running).

# FocusTrack

Distraction monitor for study sessions. Takes a webcam snapshot every 5 seconds, estimates head pose with MediaPipe, and rings an alarm if you look away too long.

## Safe zone

| Direction | Status |
|-----------|--------|
| Laptop screen | OK |
| Desk / keyboard | OK |
| Left / right / up (away from screen) | Distracted |

Alarm starts after **2 seconds** distracted, then loops **alarm.wav** until you look back at the safe zone or close the app.

## Requirements

- Windows (built-in laptop webcam)
- Python 3.12+ with dependencies installed in `../venv-win`

```powershell
cd D:\Projects\focustrack
python -m venv venv-win
.\venv-win\Scripts\pip install -r focustrack\requirements.txt
```

## Run

Double-click `run.bat` or:

```powershell
cd D:\Projects\focustrack\focustrack
..\venv-win\Scripts\python.exe main.py
```

### Options

```powershell
# Test alarm sound only (5 seconds)
..\venv-win\Scripts\python.exe main.py --test-alarm

# Print yaw/pitch/roll every snapshot (tune angles in config.py)
..\venv-win\Scripts\python.exe main.py --calibrate

```

Every snapshot is saved under `snapshots/` with labels burned into the image:
`YYYYMMDD_HHMMSS_FOCUSED.jpg`, `..._DISTRACTED.jpg`, or `..._NO_FACE.jpg`

### Stop background process

Double-click `stop.bat` or run in PowerShell:

```powershell
Get-CimInstance Win32_Process -Filter "name='python.exe'" |
  Where-Object { $_.CommandLine -like '*focustrack*main.py*' } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
```

## Configuration

Edit `config.py` to change:

- `SNAPSHOT_INTERVAL_SEC` (default: 5)
- `YAW_MIN` / `YAW_MAX` / `PITCH_MIN` / `PITCH_MAX`
- Alarm timing (`ALARM_ON_SEC`, `ALARM_OFF_SEC`, `ALARM_TOTAL_SEC`)

## Background use

Run in a separate PowerShell window and minimize it:

```powershell
cd D:\Projects\focustrack\focustrack
Start-Process -WindowStyle Minimized ..\venv-win\Scripts\python.exe -ArgumentList "main.py"
```

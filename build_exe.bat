@echo off
echo Building IP Ping Checker executable...

REM Install dependencies
pip install -r requirements.txt

REM Build executable
pyinstaller --onefile --windowed --name "IPPingChecker" --icon=app.ico ping_app.py

echo.
echo Build complete! The executable is in the 'dist' folder.
echo.
pause

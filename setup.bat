@echo off
echo Setting up IP Ping Checker development environment...

REM Create virtual environment
python -m venv venv

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
pip install -r requirements.txt

echo.
echo Setup complete! To run the application:
echo 1. Activate virtual environment: venv\Scripts\activate.bat
echo 2. Run application: python ping_app.py
echo.
echo To build executable: run build_exe.bat
echo.
pause

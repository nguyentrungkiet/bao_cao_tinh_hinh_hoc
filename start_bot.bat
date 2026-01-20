@echo off
REM Script to start Telegram Score Bot
REM Ensure this file is saved with UTF-8 encoding

cd /d C:\bao_cao_tinh_hinh_hoc

REM Activate virtual environment and run bot
call .venv\Scripts\activate.bat
python main.py

REM If bot crashes, wait 10 seconds and restart
timeout /t 10
goto :start

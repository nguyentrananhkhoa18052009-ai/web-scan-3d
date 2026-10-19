@echo off
title He Thong Do Toa Do 3D
color 0a
cd /d "%~dp0"
call venv\Scripts\activate
start http://127.0.0.1:5000
python app.py
pause

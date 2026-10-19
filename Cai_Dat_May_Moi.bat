@echo off
title Cai Dat Moi Truong 3D
color 0a
echo Dang tao moi truong ao...
python -m venv venv
echo Dang kich hoat moi truong...
call venv\Scripts\activate
echo Dang cai dat thu vien tu requirements.txt...
pip install -r requirements.txt
echo Hoan tat cai dat! Tu gio ban chi can mo file Chay_Web.bat
pause

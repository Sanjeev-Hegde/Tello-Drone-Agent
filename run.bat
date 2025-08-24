@echo off
REM Activate virtual environment and run the application

call venv\Scripts\activate.bat
python src\main.py %*

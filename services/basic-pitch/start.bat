@echo off
echo Starting Basic Pitch transcription service...
call "%~dp0venv\Scripts\activate"
python "%~dp0app.py"

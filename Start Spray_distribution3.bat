@echo off
REM Byt ut "Spray_distribution.py" mot namnet på din egen fil om den heter något annat
set SCRIPT_NAME=Spray_distribution3.py

echo Startar sprayfärgsimuleringen med Streamlit...
echo ----------------------------------

REM Kontrollera om Python finns installerat
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Fel: Python hittades inte eller ar inte tillagt i systemets PATH.
    pause
    exit /b
)

REM Kör Streamlit via python -m för att garantera att det hittas
python -m streamlit run %SCRIPT_NAME%

echo.
echo ----------------------------------
echo Programmet har avslutats.
pause
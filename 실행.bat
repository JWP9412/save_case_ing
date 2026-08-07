@echo off
REM case-ing GUI 실행 (더블클릭용)
REM 이 bat이 있는 폴더(=프로젝트 루트)로 이동한 뒤 main.py 를 실행합니다.
cd /d "%~dp0"
python main.py
if errorlevel 1 (
    echo.
    echo [오류] 실행에 실패했습니다. Python이 PATH에 있는지, main.py가 있는지 확인하세요.
    pause
)

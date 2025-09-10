@echo off
echo Windows 바로가기 생성 중...

set "TARGET_PATH=%~dp0실시간-캡차-처리.bat"
set "SHORTCUT_PATH=%USERPROFILE%\Desktop\실시간-캡차-처리.lnk"

powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%SHORTCUT_PATH%'); $Shortcut.TargetPath = '%TARGET_PATH%'; $Shortcut.WorkingDirectory = '%~dp0'; $Shortcut.Description = '실시간 캡차 처리 시스템'; $Shortcut.Save()"

echo ✅ 바로가기가 바탕화면에 생성되었습니다!
echo    파일: %SHORTCUT_PATH%
pause

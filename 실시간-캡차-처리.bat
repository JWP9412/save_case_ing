@echo off
echo ========================================
echo    실시간 캡차 처리 시스템 실행
echo ========================================
echo.

cd /d "%~dp0"
echo 현재 위치: %CD%
echo.

echo 파이썬 의존성 확인 중...
python -c "import PIL; print('✅ Pillow 설치됨')" 2>nul || (
    echo ❌ Pillow가 설치되지 않음. 설치 중...
    pip install Pillow
)

echo.
echo Cypress 실행 중...
echo 브라우저가 열리면 파이썬 입력창이 나타납니다.
echo 6글자 캡차를 입력해주세요!
echo.

npx cypress run --spec "cypress/e2e/realtime-captcha-automation.cy.js" --headed

echo.
echo ========================================
echo    실행 완료!
echo ========================================
pause

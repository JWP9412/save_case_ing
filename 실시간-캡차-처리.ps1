# 실시간 캡차 처리 시스템 실행 스크립트
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "    실시간 캡차 처리 시스템 실행" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 현재 디렉토리로 이동
Set-Location $PSScriptRoot
Write-Host "현재 위치: $(Get-Location)" -ForegroundColor Green
Write-Host ""

# 파이썬 의존성 확인
Write-Host "파이썬 의존성 확인 중..." -ForegroundColor Yellow
try {
    python -c "import PIL; print('✅ Pillow 설치됨')" 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Pillow not installed"
    }
} catch {
    Write-Host "❌ Pillow가 설치되지 않음. 설치 중..." -ForegroundColor Red
    pip install Pillow
}

Write-Host ""
Write-Host "Cypress 실행 중..." -ForegroundColor Yellow
Write-Host "브라우저가 열리면 파이썬 입력창이 나타납니다." -ForegroundColor Cyan
Write-Host "6글자 캡차를 입력해주세요!" -ForegroundColor Cyan
Write-Host ""

# Cypress 실행
npx cypress run --spec "cypress/e2e/realtime-captcha-automation.cy.js" --headed

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "    실행 완료!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Read-Host "Enter 키를 눌러 종료하세요"

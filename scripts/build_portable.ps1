#Requires -Version 5.1
<#
.SYNOPSIS
  case-ing Windows 포터블 폴더(case-ing-portable)를 조립합니다.

.DESCRIPTION
  1) PyInstaller로 CaseIng.exe(onedir) 빌드
  2) Node.js Windows x64 포터블을 runtime/node 에 배치
  3) src, node_modules, package.json, ocr_export, assets, docs 복사
  4) api/certification 안내 README 배치

  사전 준비:
  - Python 3.10+ + pip install -r requirements.txt + pip install pyinstaller
  - Node.js/npm (빌드 PC에서 npm install 용)
  - 인터넷 (Node zip·Puppeteer Chromium 다운로드)

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts/build_portable.ps1
#>

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

$OutName = "case-ing-portable"
$OutDir = Join-Path $Root $OutName
$DistExeDir = Join-Path $Root "dist\CaseIng"
$NodeVersion = "20.18.1"
$NodeZipName = "node-v$NodeVersion-win-x64"
$NodeZipUrl = "https://nodejs.org/dist/v$NodeVersion/$NodeZipName.zip"
$CacheDir = Join-Path $Root ".portable_cache"

Write-Host "=== case-ing portable build ===" -ForegroundColor Cyan
Write-Host "Root: $Root"

# --- 0. 도구 확인 ---
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "python 이 PATH에 없습니다."
}
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw "npm 이 PATH에 없습니다. (빌드 PC에서 node_modules 생성용)"
}

# --- 1. PyInstaller ---
Write-Host "`n[1/5] PyInstaller (CaseIng.spec) ..." -ForegroundColor Yellow
python -m pip install -q "pyinstaller>=6.0"
if (-not (Test-Path (Join-Path $Root "CaseIng.spec"))) {
    throw "CaseIng.spec 이 없습니다."
}
python -m PyInstaller --noconfirm --clean CaseIng.spec
if (-not (Test-Path (Join-Path $DistExeDir "CaseIng.exe"))) {
    throw "빌드 실패: dist\CaseIng\CaseIng.exe 없음"
}

# --- 2. 출력 폴더 초기화 + exe/_internal 복사 ---
Write-Host "`n[2/5] Assemble $OutName ..." -ForegroundColor Yellow
if (Test-Path $OutDir) {
    Remove-Item -Recurse -Force $OutDir
}
New-Item -ItemType Directory -Path $OutDir | Out-Null
Copy-Item -Recurse -Force (Join-Path $DistExeDir "*") $OutDir

# --- 3. Node 포터블 ---
Write-Host "`n[3/5] Bundle Node.js $NodeVersion ..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path $CacheDir -Force | Out-Null
$ZipPath = Join-Path $CacheDir "$NodeZipName.zip"
$ExtractDir = Join-Path $CacheDir $NodeZipName
if (-not (Test-Path $ZipPath)) {
    Write-Host "Downloading $NodeZipUrl ..."
    Invoke-WebRequest -Uri $NodeZipUrl -OutFile $ZipPath
}
if (-not (Test-Path (Join-Path $ExtractDir "node.exe"))) {
    if (Test-Path $ExtractDir) { Remove-Item -Recurse -Force $ExtractDir }
    Expand-Archive -Path $ZipPath -DestinationPath $CacheDir -Force
}
$RuntimeNode = Join-Path $OutDir "runtime\node"
New-Item -ItemType Directory -Path (Join-Path $OutDir "runtime") -Force | Out-Null
if (Test-Path $RuntimeNode) { Remove-Item -Recurse -Force $RuntimeNode }
Copy-Item -Recurse -Force $ExtractDir $RuntimeNode
if (-not (Test-Path (Join-Path $RuntimeNode "node.exe"))) {
    throw "runtime\node\node.exe 복사 실패"
}

# --- 4. src + npm + Chromium + ocr_export + assets + docs ---
Write-Host "`n[4/5] Copy src, node_modules, ocr_export, assets ..." -ForegroundColor Yellow
if (-not (Test-Path (Join-Path $Root "node_modules"))) {
    Write-Host "npm install (project root) ..."
    npm install
}

# Chrome을 프로젝트 안 runtime/puppeteer 에 설치 (.puppeteerrc.cjs가 위치 지정)
# 이유: 기본값(~/.cache/puppeteer)이면 포터블 폴더에 Chrome이 안 들어가서
#       다른 PC에서 "Could not find Chrome" 오류가 남
$PuppeteerCache = Join-Path $Root "runtime\puppeteer"
if (-not (Test-Path (Join-Path $PuppeteerCache "chrome"))) {
    Write-Host "Installing Chrome into runtime\puppeteer ..."
    # 환경변수가 .puppeteerrc.cjs보다 우선하므로 설치 위치를 확실히 고정
    $env:PUPPETEER_CACHE_DIR = $PuppeteerCache
    npx puppeteer browsers install chrome
    Remove-Item Env:\PUPPETEER_CACHE_DIR -ErrorAction SilentlyContinue
}
if (-not (Test-Path (Join-Path $PuppeteerCache "chrome"))) {
    throw "Chrome install failed: runtime\puppeteer\chrome not found"
}
Copy-Item -Recurse -Force $PuppeteerCache (Join-Path $OutDir "runtime\puppeteer")
Copy-Item -Force (Join-Path $Root ".puppeteerrc.cjs") (Join-Path $OutDir ".puppeteerrc.cjs")

Copy-Item -Recurse -Force (Join-Path $Root "src") (Join-Path $OutDir "src")
Copy-Item -Force (Join-Path $Root "package.json") (Join-Path $OutDir "package.json")
if (Test-Path (Join-Path $Root "package-lock.json")) {
    Copy-Item -Force (Join-Path $Root "package-lock.json") (Join-Path $OutDir "package-lock.json")
}
Copy-Item -Recurse -Force (Join-Path $Root "node_modules") (Join-Path $OutDir "node_modules")
Copy-Item -Recurse -Force (Join-Path $Root "ocr_export") (Join-Path $OutDir "ocr_export")
if (Test-Path (Join-Path $Root "assets")) {
    Copy-Item -Recurse -Force (Join-Path $Root "assets") (Join-Path $OutDir "assets")
}

$DocsOut = Join-Path $OutDir "docs"
New-Item -ItemType Directory -Path $DocsOut -Force | Out-Null
foreach ($doc in @("DEPLOY_WINDOWS.md", "PORTABLE_LAYOUT.md")) {
    $srcDoc = Join-Path $Root "docs\$doc"
    if (Test-Path $srcDoc) {
        Copy-Item -Force $srcDoc (Join-Path $DocsOut $doc)
    }
}

# 포터블 사용자용 README.TXT (폴더 맨 위 — 메모장으로 바로 열림)
$PortableReadmeSrc = Join-Path $Root "docs\README_PORTABLE.txt"
if (Test-Path $PortableReadmeSrc) {
    Copy-Item -Force $PortableReadmeSrc (Join-Path $OutDir "README.TXT")
}

# certification 자리
$CertOut = Join-Path $OutDir "api\certification"
New-Item -ItemType Directory -Path $CertOut -Force | Out-Null
$CertReadmeSrc = Join-Path $Root "api\certification\README.md"
if (Test-Path $CertReadmeSrc) {
    Copy-Item -Force $CertReadmeSrc (Join-Path $CertOut "README.md")
}
# 선택: 빌드 PC에 client_secret이 있으면 복사(배포 zip에 비밀이 들어가니 주의)
$SecretSrc = Join-Path $Root "api\certification\client_secret.json"
if (Test-Path $SecretSrc) {
    Write-Host "WARNING: client_secret.json found — copying into portable (handle zip carefully)" -ForegroundColor Magenta
    Copy-Item -Force $SecretSrc (Join-Path $CertOut "client_secret.json")
}

New-Item -ItemType Directory -Path (Join-Path $OutDir "data") -Force | Out-Null
Set-Content -Path (Join-Path $OutDir "data\.gitkeep") -Value "" -Encoding UTF8

# --- 5. 요약 ---
Write-Host "`n[5/5] Done." -ForegroundColor Green
Write-Host "Output: $OutDir"
Write-Host "Run:   $OutDir\CaseIng.exe"
Write-Host "See:   $OutDir\docs\DEPLOY_WINDOWS.md"
Write-Host ""
Write-Host "Installed / used by this script:"
Write-Host "  - pyinstaller (pip)"
Write-Host "  - Node.js portable zip v$NodeVersion (-> runtime\node)"
Write-Host "  - project node_modules (npm install if missing)"

# -*- mode: python ; coding: utf-8 -*-
"""
CaseIng.exe PyInstaller 스펙 (onedir)

빌드:
  pyinstaller CaseIng.spec

산출물: dist/CaseIng/CaseIng.exe + _internal/
이후 scripts/build_portable.ps1 이 case-ing-portable/ 로 조립합니다.
"""
import sys
from PyInstaller.utils.hooks import collect_all, collect_data_files

block_cipher = None

# EasyOCR / customtkinter 등 데이터·숨은 import 수집
datas = []
binaries = []
hiddenimports = [
    "customtkinter",
    "PIL",
    "PIL.Image",
    "PIL.ImageTk",
    "gspread",
    "google.auth",
    "google.auth.transport.requests",
    "google_auth_oauthlib",
    "google_auth_oauthlib.flow",
    "google.oauth2.credentials",
    "google.oauth2.service_account",
    "googleapiclient",
    "psutil",
    "cv2",
    "numpy",
    "pytesseract",
]

for pkg in ("customtkinter", "easyocr", "torchvision", "skimage"):
    try:
        d, b, h = collect_all(pkg)
        datas += d
        binaries += b
        hiddenimports += h
    except Exception:
        pass

# 프로젝트 리소스 (exe 옆에도 복사하지만, 빌드에 넣어 두면 안전)
datas += collect_data_files("customtkinter", includes=["**/*.json", "**/*.tcl"])

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="CaseIng",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # GUI: 콘솔 창 숨김
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Windows exe / 바로가기 아이콘 (미어캣+저울)
    icon="assets/app_icon.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="CaseIng",
)

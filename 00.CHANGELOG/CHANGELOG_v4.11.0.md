# CHANGELOG v4.11.0

## v4.11.0 주요 변경 (2026-08-07)

### Features & Improvements

- **앱 아이콘 (미어캣 + 저울)**
  - 공식 아이콘 `assets/app_icon.png` / `assets/app_icon.ico` 추가.
  - 미어캣 얼굴 누끼 + 픽셀아트 저울 + 보노보노식 식은땀 합성.
  - 창·작업표시줄: `gui/utils/window_bootstrap.py`에서 아이콘 적용.
  - PyInstaller `CaseIng.spec`에 exe 아이콘(`assets/app_icon.ico`) 연결.
  - 로컬 실행용 `실행.bat` 추가.

### 이전 버전 요약 (v4.10.0)

- UI 이모지 정리, 메일 요약 누적(전체 사건), 특정 기간 조회, 시트-대법원 대조.

## Technical

- `config.py`: `APP_VERSION = "4.11.0"`, `APP_ICON_PNG`, `APP_ICON_ICO`.
- `gui/utils/window_bootstrap.py`: `_apply_window_icon`.
- `CaseIng.spec`: `icon="assets/app_icon.ico"`.
- `assets/app_icon.png`, `assets/app_icon.ico`.
- `실행.bat`.

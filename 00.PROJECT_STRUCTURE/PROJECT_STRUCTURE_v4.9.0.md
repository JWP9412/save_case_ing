# 프로젝트 구조 (Project Structure) - v4.9.0

## Root Directory
- **`config.py`** (v4.9.0): `APP_VERSION = "4.9.0"`, `get_base_dir` / `BASE_DIR` / `path_from_base`, OAuth·캘린더·시트 할당량 상수, **`OCR_*`**.
- **`main.py`**, **`auto_runner.py`**, **`data/`**, **`logs/`**: 이전과 동일 역할. 데이터/로그 경로는 BASE_DIR 기준.
- **`CaseIng.spec`**, **`scripts/build_portable.ps1`**, **`requirements-build.txt`**: Windows 포터블 빌드.
- **`.puppeteerrc.cjs`**: Puppeteer Chrome 캐시를 `runtime/puppeteer`로 고정.

## ocr_export/
- **`captcha_ocr.py`**: EasyOCR + Tesseract 캡차 OCR.
- (선택) `captcha_model.py`, `train_captcha_model.py`: CNN 학습용(미배포 모델 시 미사용).

## gui/ (UI)
- **`app_controller.py`**: `set_captcha_input`, `set_captcha_entry_locked` 위임.
- **`utils/captcha_ui.py`**: OCR 입력 채우기·잠금·수동 폴백(스레드 안전).
- **`utils/google_sheet_ui.py`**: 캐시/숨김 경로 `path_from_base`.
- **`utils/batch_actions.py`**, **`dialogs/settings_dialog.py`**, **`panels/control_panel.py`**: v4.8.0/v4.7.0과 동일 역할.

## services/ (Business Logic)
- **`captcha_ocr_service.py`** (v4.9.0 신규): `ocr_export` 래퍼.
- **`process_controller.py`** (v4.9.0): OCR 웨이브·자동 제출·재시도·수동 폴백 (+ v4.8.0 시트 저장 직렬화).
- **`puppeteer.py`** (v4.9.0): 동봉 `runtime/node/node.exe`, `cwd=BASE_DIR`.
- **`google_sheets.py`**: v4.8.0 할당량 완화 유지.
- **`email_manager.py`**, **`logger_service.py`**: BASE_DIR 경로.
- **`google_oauth.py`**, **`google_calendar.py`**: 이전과 동일.

## docs/, api/certification/
- **`docs/DEPLOY_WINDOWS.md`**, **`docs/PORTABLE_LAYOUT.md`**, **`docs/README_PORTABLE.txt`**: 포터블 배포·사용자 안내.
- **`api/certification/README.md`**: `client_secret.json` + 구글 시트 준비 요약.
- **`00.CHANGELOG/`**, **`00.README/`**, **`00.PROJECT_STRUCTURE/`**: v4.9.0 문서 추가.

## src/, gas/
- **`src/`**: Puppeteer 크롤링 (`interactive_runner.js` 등).
- **`gas/`**: 알림메일 즉시 발송.

---

## 트리 형식 (요약)

```
case-ing/
├── config.py                      # APP_VERSION 4.9.0, BASE_DIR, OCR_*
├── CaseIng.spec                   # PyInstaller onedir
├── .puppeteerrc.cjs               # Chrome → runtime/puppeteer
├── scripts/build_portable.ps1     # 포터블 조립
├── ocr_export/
│   └── captcha_ocr.py
├── services/
│   ├── captcha_ocr_service.py
│   ├── process_controller.py      # OCR 웨이브 + 시트 저장
│   ├── puppeteer.py               # 동봉 Node
│   └── google_sheets.py
├── gui/utils/captcha_ui.py
├── docs/
│   ├── DEPLOY_WINDOWS.md
│   ├── PORTABLE_LAYOUT.md
│   └── README_PORTABLE.txt
├── api/certification/README.md
└── ...
```

# 프로젝트 구조 (Project Structure) - v5.3.0

## Root Directory

- **`config.py`**: `APP_VERSION = "5.3.0"`, `PROFILE_COUNT`, OCR·캐시·스크린샷·알림메일 상수. `load_user_settings()`.
- **`main.py`**: GUI / `--auto` 진입점. 시작 시 `load_user_settings()`.
- **`auto_runner.py`**: CLI 일괄 자동 조회. **반드시** `load_user_settings()` 호출.
- **`AGENTS.md`**: 프로젝트 규칙 (진입점·설정 로드 보호 포함).
- **`requirements.txt`**: Python 의존성.

## gui/

- **`app_controller.py`**: 메인 컨트롤러.
- **`dialogs/settings_dialog.py`**: 프로필 수, 알림 수신 메일 등.
- **`panels/progress_panel.py`**: 진행상황 로그.
- **`utils/`**: captcha_ui, google_sheet_ui, window_lifecycle 등.

## services/

- **`puppeteer.py`**: 레인 워커, `_drain_worker_stdout`, taskkill 숨김.
- **`finalized_case.py`**: 종국 판별(기본내용 종국결과 칸만)·숨김 후보.
- **`profile_maintenance.py`**: 프로필 캐시·백업.
- **`email_manager.py`**: 메일 요약.
- **`process_controller/`**
  - `case_runner.py` — 배치·프로필=레인·CLI 자동
  - `captcha_ocr.py`, `result_handler.py`, `cleanup.py`, `controller.py`

## src/

- **`interactive_runner.js`**: `--worker` 상주. 스마트 스킵(폼 대기·스캔), about:blank 미사용.
- **`PageController.js`**: `waitForSearchForm`, `scanRecentCase`, 탭/그리드.

## 99.Error case/

- 사고 기록. v5.3.0 관련: `ERROR_20260909_*.md` (IDLE 오판, 스마트 스킵, 종국 오탐, CLI 설정).

## 문서

- `00.CHANGELOG/CHANGELOG_v5.3.0.md`
- `00.README/README_v5.3.0.md`
- `00.PROJECT_STRUCTURE/PROJECT_STRUCTURE_v5.3.0.md`

## 트리 형식 (요약)

```
case-ing/
├── config.py                         # 5.3.0, load_user_settings
├── auto_runner.py                    # CLI + load_user_settings
├── AGENTS.md
├── services/
│   ├── puppeteer.py                  # IDLE drain, CREATE_NO_WINDOW
│   ├── finalized_case.py             # 종국결과 칸만
│   └── process_controller/
├── src/
│   ├── interactive_runner.js
│   └── PageController.js             # waitForSearchForm, scanRecentCase
└── 99.Error case/ERROR_20260909_*.md
```

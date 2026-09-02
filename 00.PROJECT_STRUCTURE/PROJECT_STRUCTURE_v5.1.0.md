# 프로젝트 구조 (Project Structure) - v5.1.0

## Root Directory

- **`config.py`**: `APP_VERSION = "5.1.0"`, `APP_TITLE = "미어캣싱"`, 사용자 설정·OCR·시트 상수.
- **`main.py`**: GUI / `--auto` 진입점.
- **`auto_runner.py`**: CLI 일괄 자동 조회.
- **`requirements.txt`**: Python 의존성.

## gui/

- **`app_controller.py`**: 메인 컨트롤러.
- **`dialogs/manual_captcha_dialog.py`**: 수동 캡차 모아보기 (화면 안에 표시·포커스).
- **`dialogs/settings_dialog.py`**, **`hearing_calendar_dialog.py`** 등.
- **`panels/progress_panel.py`**: 진행상황 로그·스크롤바.
- **`panels/control_panel.py`**, **`case_row.py`**, **`case_list_panel.py`**.

## services/

- **`process_controller/`** (v5.1.0 패키지 분리)
  - `controller.py` — mixin 조합 + Puppeteer 래퍼
  - `captcha_ocr.py` — OCR 웨이브·수동 창·자동 제출
  - `result_handler.py` — 시트 비교·저장·finish_* (8/12 사고 가드)
  - `case_runner.py` — 배치·레인·CLI
  - `hearing.py` — 기일·캘린더
  - `cleanup.py` — 브라우저 정리
- **`email_manager.py`**: 알림메일 (`updates` + `result_changes`).
- **`google_sheets.py`**, **`puppeteer.py`**, **`crash_guard.py`** 등.

## src/

- Puppeteer(Node): `PageController.js`, `interactive_runner.js`.

## 문서·사고 기록

- `00.CHANGELOG/CHANGELOG_v5.1.0.md`
- `00.README/README_v5.1.0.md`
- `99.Error case/` — 데이터 사고 기록 (재발 방지용)
- 루트 `README.md`

## 트리 형식 (요약)

```
case-ing/
├── config.py                         # 5.1.0
├── main.py
├── auto_runner.py
├── gui/
│   ├── app_controller.py
│   └── dialogs/manual_captcha_dialog.py
├── services/
│   ├── process_controller/           # mixin 패키지 (구 process_controller.py)
│   │   ├── __init__.py
│   │   ├── controller.py
│   │   ├── captcha_ocr.py
│   │   ├── result_handler.py
│   │   ├── case_runner.py
│   │   ├── hearing.py
│   │   └── cleanup.py
│   ├── email_manager.py
│   └── google_sheets.py
├── src/                              # Puppeteer
├── 99.Error case/
└── 00.CHANGELOG / 00.README / ...
```

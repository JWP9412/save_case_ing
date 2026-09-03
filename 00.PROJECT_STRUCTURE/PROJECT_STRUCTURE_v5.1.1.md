# 프로젝트 구조 (Project Structure) - v5.1.1

## Root Directory

- **`config.py`**: `APP_VERSION = "5.1.1"`, `APP_TITLE = "미어캣싱"`, 사용자 설정·OCR·시트 상수.
- **`main.py`**: GUI / `--auto` 진입점.
- **`auto_runner.py`**: CLI 일괄 자동 조회.
- **`requirements.txt`**: Python 의존성.

## gui/

- **`app_controller.py`**: 메인 컨트롤러.
- **`panels/progress_panel.py`**: 진행상황 Canvas 로그, CTkScrollbar, 「전체 복사」.
- **`dialogs/manual_captcha_dialog.py`**: 수동 캡차 모아보기.
- **`panels/control_panel.py`**, **`case_row.py`**, **`case_list_panel.py`**.

## services/

- **`process_controller/`** (mixin 패키지)
  - `case_runner.py` — 배치 시작/중지 (`start_processing` 등)
  - `hearing.py` — 기일 추출 (`_normalize_text` staticmethod)
  - `captcha_ocr.py`, `result_handler.py`, `cleanup.py`, `controller.py`
- **`email_manager.py`**, **`google_sheets.py`**, **`puppeteer.py`** 등.

## src/

- Puppeteer(Node): `PageController.js`, `interactive_runner.js`.

## 문서·사고 기록

- `00.CHANGELOG/CHANGELOG_v5.1.1.md`
- `00.README/README_v5.1.1.md`
- `99.Error case/`
- 루트 `README.md`

## 트리 형식 (요약)

```
case-ing/
├── config.py                         # 5.1.1
├── gui/panels/progress_panel.py      # 스크롤바·전체 복사
├── services/process_controller/
│   ├── case_runner.py
│   └── hearing.py
└── 00.CHANGELOG / 00.README / ...
```

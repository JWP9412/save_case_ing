# 프로젝트 구조 (Project Structure) - v4.6.3

## Root Directory
- **`config.py`** (v4.6.3): `APP_VERSION = "4.6.3"`.
- **`main.py`**, **`auto_runner.py`**, **`data/`**, **`logs/`**: v4.6.2와 동일.

## gui/ (UI)
- **`app_controller.py`**: `remove_duplicates_for_selected_cases` — 선택 사건 시트 중복 행 제거(백그라운드 스레드 + ui_queue).
- **`panels/control_panel.py`**: `dedup_btn` 「🧹 중복 오류 제거」.
- 그 외 panels/dialogs/utils: v4.6.2와 동일 역할.

## services/ (Business Logic)
- **`process_controller.py`**: `filter_new_data` 역순 탐색(중복 무한 증식 방지).
- **`google_sheets.py`**: `remove_duplicate_rows_from_sheet`, `_is_progress_data_row`, `_sheet_row_dedup_key`.
- 그 외: v4.6.2와 동일.

## src/, gas/, 문서
- **`src/`**: Puppeteer.
- **`00.CHANGELOG/`**, **`00.README/`**, **`00.PROJECT_STRUCTURE/`**: v4.6.3 문서 추가.

---

## 트리 형식 (요약)

```
case-ing/
├── config.py
├── services/
│   ├── process_controller.py   # filter_new_data 역순
│   └── google_sheets.py        # remove_duplicate_rows_from_sheet
├── gui/
│   ├── app_controller.py       # remove_duplicates_for_selected_cases
│   └── panels/control_panel.py # dedup_btn
└── ...
```

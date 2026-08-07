# 프로젝트 구조 (Project Structure) - v4.10.0

## Root Directory
- **`config.py`** (v4.10.0): `APP_VERSION = "4.10.0"`, `UI_USE_EMOJI`, `BTN_TEXT_*`, OCR/BASE_DIR 등.
- **`main.py`**, **`auto_runner.py`**: CLI는 `record_run_results`로 GUI와 결과 공유, 변경없음 분리.
- **`data/unsent_emails.json`**: `updates` + **`run_results`** (조회 결과 누적).

## gui/
- **`panels/control_panel.py`**: 3행 버튼(기간 조회·시트 대조), 안전 문자 문구.
- **`utils/glyphs.py`**: 이모지 sanitize.
- **`utils/batch_actions.py`**: 기간 조회·시트 대조 플래그 설정.
- **`utils/email_ui.py`**: `all_cases` 전달.
- **`dialogs/date_picker.py`**, **`period_query_dialog.py`**, **`report_preview_dialog.py`**.
- **`app_controller.py`**: 특수 모드 플래그, 이력 mtime 폴링.

## services/
- **`email_manager.py`**: `record_run_results`, 전체 사건 기준 요약(미조회 포함).
- **`date_utils.py`**: 유연한 날짜 파서.
- **`sheet_compare.py`**: 행 존재 여부·전체 내용 대조.
- **`period_report.py`**: HTML/MD 렌더러.
- **`process_controller.py`**: `is_period_mode` / `is_compare_mode` 처리·미리보기.

## 문서
- **`00.CHANGELOG/CHANGELOG_v4.10.0.md`**, **`00.README/README_v4.10.0.md`**, 본 파일.

## 트리 형식 (요약)

```
case-ing/
├── config.py                      # 4.10.0, BTN_TEXT_*, UI_USE_EMOJI
├── auto_runner.py                 # run_results 공유
├── services/
│   ├── email_manager.py           # record_run_results
│   ├── date_utils.py
│   ├── sheet_compare.py
│   ├── period_report.py
│   └── process_controller.py      # 기간/대조 모드
├── gui/
│   ├── utils/glyphs.py
│   ├── utils/batch_actions.py
│   ├── panels/control_panel.py
│   └── dialogs/
│       ├── date_picker.py
│       ├── period_query_dialog.py
│       └── report_preview_dialog.py
└── ...
```

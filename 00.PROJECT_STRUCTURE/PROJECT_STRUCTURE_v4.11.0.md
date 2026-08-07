# 프로젝트 구조 (Project Structure) - v4.11.0

## Root Directory
- **`config.py`** (v4.11.0): `APP_VERSION = "4.11.0"`, `APP_ICON_PNG` / `APP_ICON_ICO`, `UI_USE_EMOJI`, `BTN_TEXT_*`.
- **`CaseIng.spec`**: exe 아이콘 `assets/app_icon.ico`.
- **`실행.bat`**: `python main.py` 더블클릭 실행.
- **`assets/app_icon.png`**, **`assets/app_icon.ico`**: 공식 앱 아이콘.
- **`main.py`**, **`auto_runner.py`**: CLI는 `record_run_results`로 GUI와 결과 공유.

## gui/
- **`utils/window_bootstrap.py`**: `_apply_window_icon` (ico + png).
- **`panels/control_panel.py`**: 기간 조회·시트 대조 버튼, 안전 문자 문구.
- **`utils/glyphs.py`**, **`utils/batch_actions.py`**, **`utils/email_ui.py`**.
- **`dialogs/date_picker.py`**, **`period_query_dialog.py`**, **`report_preview_dialog.py`**, **`first_run_dialog.py`**.

## services/
- **`email_manager.py`**: `record_run_results`, 전체 사건 기준 요약.
- **`date_utils.py`**, **`sheet_compare.py`**, **`period_report.py`**.
- **`process_controller.py`**: `is_period_mode` / `is_compare_mode`.
- **`sheet_setup.py`**, **`google_oauth.py`**.

## 문서
- **`00.CHANGELOG/CHANGELOG_v4.11.0.md`**, **`00.README/README_v4.11.0.md`**, 본 파일.
- (직전) **`CHANGELOG_v4.10.0.md`** 등.

## 트리 형식 (요약)

```
case-ing/
├── config.py                      # 4.11.0, APP_ICON_*
├── CaseIng.spec                   # icon=assets/app_icon.ico
├── 실행.bat
├── assets/
│   ├── app_icon.png
│   └── app_icon.ico
├── gui/utils/window_bootstrap.py  # 창 아이콘
├── services/                      # 기간조회·메일누적·대조 (v4.10+)
└── ...
```

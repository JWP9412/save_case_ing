# 프로젝트 구조 (Project Structure) - v4.13.0

## Root Directory
- **`config.py`** (v4.13.0): `APP_VERSION`, `BTN_TEXT_SHEET_MGMT`(`사건 시트 관리 ▾`).

## gui/
- **`utils/ui_queue_manager.py`**: 기간조회 완료 등 성공 계열 행 배경 초록.
- **`dialogs/report_preview_dialog.py`**: Markdown 기본 탭(순서 MD→HTML).
- **`panels/control_panel.py`**: 시트 관리 버튼 ▾ 문구.

## services/
- **`process_controller.py`**: 기간/대조 실패 재실행, 프로필 락(cleanup까지), 레인=instance_N, 기간 상태문구, `touch_last_query_time` 호출.
- **`google_sheets.py`**: footer `업데이트 일시`+`최근 조회 일시`, `touch_last_query_time`.
- **`date_utils.py`**: `format_date_yy` (`YY.MM.DD.`).

## 문서
- **`00.CHANGELOG/CHANGELOG_v4.13.0.md`**, **`00.README/README_v4.13.0.md`**, 본 파일.

## 트리 형식 (요약)

```
case-ing/
├── config.py                      # 4.13.0
├── services/process_controller.py # 재실행·프로필락·기간상태
├── services/google_sheets.py      # 최근 조회 일시
├── gui/dialogs/report_preview_dialog.py
├── gui/utils/ui_queue_manager.py
└── ...
```

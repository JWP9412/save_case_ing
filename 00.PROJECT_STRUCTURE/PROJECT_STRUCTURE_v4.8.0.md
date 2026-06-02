# 프로젝트 구조 (Project Structure) - v4.8.0

## Root Directory
- **`config.py`** (v4.8.0): `APP_VERSION = "4.8.0"`, OAuth·캘린더 설정, **구글 시트 API 할당량 상수** (`GOOGLE_SHEET_MIN_INTERVAL`, `GOOGLE_SHEET_RETRY_*`, `GOOGLE_SHEET_CELL_MAX_CHARS` 등).
- **`main.py`**, **`auto_runner.py`**, **`data/`**, **`logs/`**: 이전 버전과 동일 역할.

## gui/ (UI)
- **`app_controller.py`**: 배치 특수 작업은 `batch_actions` 모듈에 위임.
- **`utils/batch_actions.py`**: 중복 제거·기록 초기화·재수집 확인 대화상자 및 플래그 설정.
- **`panels/control_panel.py`**: `dedup_btn`, `reset_btn`.
- **`dialogs/settings_dialog.py`**: 구글 OAuth 연동, 캘린더 켜기/끄기·이벤트 템플릿.

## services/ (Business Logic)
- **`google_sheets.py`** (v4.8.0 핵심 변경):
  - `RLock` 기반 `_save_lock`, `_throttle_api`, jitter 재시도 데코레이터.
  - `overwrite_progress_area(case, data, existing_values=None)` — 스냅샷 재사용·서식 `batch_update` 1회.
  - `count_progress_rows_from_values`, `get_full_sheet_data` 재시도, `_case_list_worksheet` 캐시.
  - `append_notification_mail` — 셀 최대 글자 수 truncate.
- **`process_controller.py`** (v4.8.0):
  - `_process_result_list` 저장 분기: `with gs._save_lock` 직렬화, `existing_values` 1회 읽기.
  - `_compute_new_progress_rows(..., existing_values=)`, `_verify_sheet_matches_court(..., sheet_count=)`.
- **`google_oauth.py`**, **`google_calendar.py`**: v4.7.0과 동일.
- **`email_manager.py`**, **`update_history.py`**: v4.7.0과 동일.

## src/, gas/, 문서
- **`src/`**: Puppeteer 크롤링.
- **`00.CHANGELOG/`**, **`00.README/`**, **`00.PROJECT_STRUCTURE/`**: v4.8.0 문서 추가.

---

## 트리 형식 (요약)

```
case-ing/
├── config.py                    # APP_VERSION 4.8.0, GOOGLE_SHEET_* 상수
├── services/
│   ├── google_sheets.py         # 저장 직렬화·스로틀·batch 통합
│   ├── process_controller.py    # 저장 파이프라인 락·1회 읽기
│   ├── google_oauth.py
│   └── google_calendar.py
├── gui/
│   ├── app_controller.py
│   ├── utils/batch_actions.py
│   └── panels/control_panel.py
└── ...
```

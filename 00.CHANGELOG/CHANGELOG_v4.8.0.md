# CHANGELOG v4.8.0

## v4.8.0 주요 변경 (2026-06-02)

### 버그 수정

- **구글 시트 할당량 초과(429) 완화**
  - 여러 사건을 동시 처리할 때 시트 API가 몰려 429가 반복되던 문제를 줄이기 위해 저장 파이프라인(읽기→덮어쓰기→검증)을 직렬화.
  - 시트를 사건마다 여러 번 읽던 것을 **1회 스냅샷**으로 통합해 호출 수 감소.
  - 색상·서식·열 너비 `batch_update`를 **1회**로 합쳐 API 호출 절감.
  - 429 재시도에 **지수 백오프 + jitter(무작위 흔들기)** 적용, 호출 간 최소 간격(`GOOGLE_SHEET_MIN_INTERVAL`) 도입.

- **신규 건수 오판 (+375건 등)**
  - 시트 조회 실패(429 등) 시 "전체를 신규"로 처리하던 로직 제거 → 실패 시 신규 0건·저장 보류로 안전 처리.

- **알림메일 시트 50,000자 초과**
  - 한 셀 최대 글자 수를 넘는 본문은 잘라 저장(400 INVALID_ARGUMENT 방지).

### 개선

- **메인 사건 목록 워크시트 캐시**: `update_main_remark` 시 매번 전체 탭 목록을 조회하지 않도록 캐시.
- **검증 단계 API 재읽기 제거**: 저장 직후 `overwrite` 반환 행 수로 대법원 행 수와 비교.
- **설정 상수 추가** (`config.py`): `GOOGLE_SHEET_MIN_INTERVAL`, `GOOGLE_SHEET_RETRY_MAX`, `GOOGLE_SHEET_RETRY_BASE_DELAY`, `GOOGLE_SHEET_AUTO_RESIZE_ON_SAVE`, `GOOGLE_SHEET_CELL_MAX_CHARS`.

## Technical

- `config.py`: `APP_VERSION = "4.8.0"`, 구글 시트 API 할당량 완화 상수.
- `services/google_sheets.py`:
  - `_save_lock` → `threading.RLock`, `_throttle_api`, `retry_on_quota_error` jitter·config 연동.
  - `overwrite_progress_area(existing_values=...)`, `_ensure_headers_and_remove_timestamp_rows` 스냅샷 재사용.
  - `_text_color_requests` / `_timestamp_format_requests` / `_auto_resize_requests` + 단일 `batch_update`.
  - `count_progress_rows_from_values`, `get_full_sheet_data` `@retry_on_quota_error`.
  - `_get_case_list_worksheet` 캐시, `append_notification_mail` 본문 truncate.
- `services/process_controller.py`:
  - 저장 분기 `with gs._save_lock` 직렬화, `existing_values` 1회 읽기·재사용.
  - `_compute_new_progress_rows(existing_values=...)`, `_verify_sheet_matches_court(sheet_count=...)`.

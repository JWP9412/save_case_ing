# CHANGELOG v4.14.0

## v4.14.0 주요 변경 (2026-08-11)

### Features & Improvements

- **신규 행 지연 등록 비고 (영업일)**
  - 시트에 처음 들어가는 진행내용 행의 비고:  
    `YYYY.MM.DD. 업데이트 됨 (n일 지연 등록. 영업일 기준)`
  - 영업일 = 토·일 제외(공휴일 미반영). 지연 1영업일 이상일 때만 붙임.
  - 기존 행의 E·F열은 그대로 유지. 앱 로그에도 지연 요약 출력.
  - 메일 HTML 표에는 추가하지 않음.

- **미어캣싱 제어 패널 · 기일 달력**
  - 「기일 달력」 버튼 → 앱 안 월간 달력 창 (`미어캣싱 · 기일 달력`).
  - 변론·감정·판결 기일을 색으로 구분. 이전/다음 달·오늘 이동.
  - 데이터: 조회 성공 시 저장한 `update_history.hearing_events` + 사건 목록.
  - 구글 캘린더 웹/앱이 아님. (설정 쪽 구글 캘린더 자동 등록은 기존과 별개.)

- **제품명 표기**
  - `APP_TITLE = "미어캣싱"` (창 제목 등).

### 이전 버전 요약 (v4.13.0)

- 기간조회 실패 재실행, 상태·행 초록, MD 기본, 시트관리 ▾, Code 21 완화, 최근 조회 일시.

## Technical

- `config.py`: `APP_VERSION = "4.14.0"`, `APP_TITLE`, `BTN_TEXT_HEARING_CALENDAR`, `DELAY_REMARK_*`.
- `services/date_utils.py`: `business_days_between`, `delay_business_days`, `format_delay_remark_suffix`.
- `services/google_sheets.py`: `_new_row_remark_text` (신규 비고 지연 문구).
- `services/process_controller.py`: `_log_delayed_registrations`, history에 `hearing_events` 전달.
- `services/update_history.py`: `serialize_hearing_events`, `update_case_record(..., hearing_events=)`.
- `gui/dialogs/hearing_calendar_dialog.py`: 월간 기일 달력 다이얼로그 (신규).
- `gui/panels/control_panel.py`: 3행 「기일 달력」 버튼.
- `gui/app_controller.py`: `open_hearing_calendar()`.

# 프로젝트 구조 (Project Structure) - v4.14.0

## Root Directory
- **`config.py`** (v4.14.0): `APP_VERSION`, `APP_TITLE`(`미어캣싱`), `BTN_TEXT_HEARING_CALENDAR`, `DELAY_REMARK_MIN_BUSINESS_DAYS`, `DELAY_REMARK_SUFFIX_FMT`.

## gui/
- **`panels/control_panel.py`**: 3행 「기일 달력」 버튼 → `open_hearing_calendar`.
- **`dialogs/hearing_calendar_dialog.py`**: 월간 기일 달력 (`HearingCalendarDialog`, `collect_hearing_items`).
- **`app_controller.py`**: `open_hearing_calendar()` — history + case_list로 달력 오픈.
- **`utils/history_ui.py`**: `update_case_timestamp(..., hearing_events=)`.

## services/
- **`date_utils.py`**: `business_days_between`, `delay_business_days`, `format_delay_remark_suffix`.
- **`google_sheets.py`**: `_new_row_remark_text` — 신규 행 지연 비고.
- **`process_controller.py`**: `_log_delayed_registrations`, 조회 완료 시 `hearing_events` 저장.
- **`update_history.py`**: `serialize_hearing_events`, `hearing_events` 필드.

## 문서
- **`00.CHANGELOG/CHANGELOG_v4.14.0.md`**, **`00.README/README_v4.14.0.md`**, 본 파일.

## 트리 형식 (요약)

```
case-ing/
├── config.py                           # 4.14.0, APP_TITLE, DELAY_*, BTN_TEXT_HEARING_CALENDAR
├── services/date_utils.py              # 영업일 지연
├── services/google_sheets.py           # 신규 비고 지연 문구
├── services/update_history.py          # hearing_events
├── services/process_controller.py      # 지연 로그 + hearing_events 전달
├── gui/dialogs/hearing_calendar_dialog.py  # 기일 달력 창 (신규)
├── gui/panels/control_panel.py         # 기일 달력 버튼
├── gui/app_controller.py               # open_hearing_calendar
└── ...
```

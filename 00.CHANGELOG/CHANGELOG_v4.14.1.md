# CHANGELOG v4.14.1

## v4.14.1 주요 변경 (2026-08-11)

### Features & Improvements

- **기일 달력 · hearing_info 폴백**
  - `hearing_events`가 없어도 목록용 `hearing_info`(최신 기일 1건)를 달력에 표시.
  - 재조회 없이도 기존 이력의 기일이 보임.

- **날짜 칸 안 기일 요약**
  - 클릭 없이 `• 피고(또는 사건명) 변론` 형식으로 칸 안에 표시.
  - 칸당 최대 2줄, 초과 시 `+N건 더`. 클릭 시 하단 상세는 기존과 동일.

- **버튼 위치 · 이모지**
  - 「📅 기일 달력」을 사건 목록 행의 **사건목록 관리 왼쪽**으로 이동.
  - 제어 패널 3행에서는 제거.

### 이전 버전 요약 (v4.14.0)

- 신규 행 지연 등록 비고(영업일), 기일 달력 최초 도입, `hearing_events` 저장, `APP_TITLE`.

## Technical

- `config.py`: `APP_VERSION = "4.14.1"`, `BTN_TEXT_HEARING_CALENDAR = "📅 기일 달력"`.
- `services/update_history.py`: `parse_hearing_info_to_event`, `_parse_hearing_info_parts`.
- `gui/dialogs/hearing_calendar_dialog.py`: 폴백 수집, 칸 인라인 요약 UI.
- `gui/panels/case_list_panel.py`: 기일 달력 버튼.
- `gui/panels/control_panel.py`: 3행에서 기일 달력 제거.

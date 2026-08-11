# 프로젝트 구조 (Project Structure) - v4.14.1

## Root Directory
- **`config.py`** (v4.14.1): `APP_VERSION`, `BTN_TEXT_HEARING_CALENDAR`(`📅 기일 달력`).

## gui/
- **`panels/case_list_panel.py`**: 사건목록 관리 왼쪽 「기일 달력」 버튼.
- **`panels/control_panel.py`**: 기일 달력 버튼 제거(기간 조회·버전 확인만 3행).
- **`dialogs/hearing_calendar_dialog.py`**: hearing_info 폴백, 칸 안 `• 이름 종류` 요약.

## services/
- **`update_history.py`**: `parse_hearing_info_to_event`, `_parse_hearing_info_parts`.

## 문서
- **`00.CHANGELOG/CHANGELOG_v4.14.1.md`**, **`00.README/README_v4.14.1.md`**, 본 파일.

## 트리 형식 (요약)

```
case-ing/
├── config.py                              # 4.14.1
├── services/update_history.py             # hearing_info → 이벤트
├── gui/dialogs/hearing_calendar_dialog.py # 폴백 + 칸 안 요약
├── gui/panels/case_list_panel.py          # 기일 달력 버튼 위치
└── ...
```

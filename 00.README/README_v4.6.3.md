# README v4.6.3

## 주요 변경 사항

### 1. 중복 진행내용 버그 수정 및 중복 오류 제거 (v4.6.3)
- **버그 수정**: `filter_new_data` 역순 탐색으로 동일 진행내용이 구글 시트에 무한히 쌓이던 현상 방지.
- **중복 오류 제거**: 제어 패널에서 선택 사건 시트의 중복 행(일자·내용·결과·공시문 동일) 일괄 정리.

### 2. 사건 목록 캐시 및 시작 UX (v4.6.2)
- 캐시 우선 로드, 시작 시 목록 미리 표시, F5 새로고침.

### 3. 사건목록 관리 다이얼로그 (v4.6.0)
- 적용·확인·취소 플로우, 7개 버튼 조건부 활성.

---

## Technical Updates
- `APP_VERSION`: "4.6.3"
- `services/process_controller.py`: `filter_new_data` 역순 매칭.
- `services/google_sheets.py`: `remove_duplicate_rows_from_sheet`.
- `gui/panels/control_panel.py`: `dedup_btn` (중복 오류 제거).
- `gui/app_controller.py`: `remove_duplicates_for_selected_cases`.

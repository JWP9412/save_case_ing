# README v4.7.0

## 주요 변경 사항

### 1. 구글 캘린더·OAuth·시트·메일 (v4.7.0)
- **캘린더**: 변론·감정·판결 기일을 설정에서 켠 경우에만 구글 캘린더에 자동 등록.
- **OAuth**: 시트·캘린더 동일 계정, 프로그램 설정에서 연동.
- **시트 열 밀림 수정**: 진행내용이 A~F열에만 저장되도록 수정.
- **메일 바로가기**: 알림 메일에서 해당 사건 시트로 바로 이동하는 링크.

### 2. 기록 초기화·재수집·중복 제거 (v4.7.0)
- **초기화·재수집**: 시트·로컬 기록 삭제 후 대법원에서 처음부터 다시 수집.
- **중복 오류 제거**: 대법원 실제 기록과 맞춰 잘못 쌓인 행만 정리.

### 3. 중복 진행내용 버그 수정 (v4.6.3)
- `filter_new_data` 역순 매칭으로 무한 증식 방지.

### 4. 사건 목록 캐시 (v4.6.2)
- 시작 시 캐시 우선 로드, F5 새로고침.

---

## Technical Updates
- `APP_VERSION`: "4.7.0"
- 신규: `services/google_oauth.py`, `services/google_calendar.py`, `gui/utils/batch_actions.py`
- 수정: `process_controller.py`, `google_sheets.py`, `email_manager.py`, `settings_dialog.py`, `control_panel.py`

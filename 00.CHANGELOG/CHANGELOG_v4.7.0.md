# CHANGELOG v4.7.0

## v4.7.0 주요 변경 (2026-05-20)

### 새 기능

- **구글 캘린더 자동 등록 (설정에서 켜는 사용자만)**
  - 사건 조회 시 변론기일·감정기일·판결선고기일이 있으면 구글 캘린더에 일정 등록.
  - 설정창에서 켜기/끄기, 제목·설명 문구 템플릿 지정 가능.

- **구글 계정 앱 내 연동 (OAuth)**
  - 구글 시트와 캘린더를 같은 계정으로 한 번 로그인해 사용.
  - 설정창에서 `client_secret.json` 파일 선택·연동 (첫 사용자 온보딩).

- **기록 초기화 후 다시 받기**
  - 제어 패널 **「기록 초기화 및 재수집」** 버튼.
  - 선택 사건의 구글 시트·로컬 캐시를 비운 뒤, 대법원에서 처음부터 전체 기록 다시 저장.

- **알림 메일 바로가기 링크**
  - 알림 메일 본문 사건명 아래 **바로가기** 링크로 해당 사건 구글 시트 탭 이동.

### 버그 수정

- **구글 시트 열 밀림**: 진행내용이 F열을 넘어 G열 이후에 쌓이던 문제 수정 (`A:F` 범위에 명시 저장).
- **메일 링크 오류**: API 주소 대신 브라우저에서 열 수 있는 `docs.google.com` URL 사용.
- **처리 멈춤**: 스마트 스킵(자동 클릭) 실패 시에도 다음 사건 처리가 이어지도록 수정.

### 개선

- **중복 오류 제거**: 대법원 사이트 실제 기록과 시트를 대조해 잘못 쌓인 행만 삭제.
- **코드 정리**: 배치 버튼 로직을 `gui/utils/batch_actions.py`로 분리, 사건 처리 흐름을 `_process_result_list` 한곳으로 통합.

## Technical

- `config.py`: `APP_VERSION = "4.7.0"`, 캘린더·OAuth 설정 상수.
- `services/google_oauth.py`, `services/google_calendar.py` (신규).
- `services/google_sheets.py`: `get_case_worksheet_url`, `overwrite_sheet_data`, `sync_and_remove_duplicates`, `A:F` 명시 `update`.
- `services/process_controller.py`: `_process_result_list` 통합, `tuple_return`, 웨이브 `processed_cases` 수정.
- `services/email_manager.py`: `sheet_url`, `_normalize_sheet_url`, 메일 HTML 바로가기.
- `services/update_history.py`: `clear_last_entry`.
- `gui/utils/batch_actions.py` (신규), `gui/dialogs/settings_dialog.py`, `gui/panels/control_panel.py` (`reset_btn`).
- `requirements.txt`: `google-api-python-client`.

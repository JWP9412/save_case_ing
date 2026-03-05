# CHANGELOG v4.2.0 (2026-03-05)

## Features & Improvements

- **알림메일 고도화**
  - 메일 본문을 HTML 표로 생성. 구글 시트에 적용된 글씨 색상(일자/내용/결과)을 메일에도 반영.
  - 시트(피고·사건명)별로 단락을 나누어 메일 발송. 구글 시트 탭 이름 기준 그룹화.
  - GAS 웹 앱 URL 설정 시 버튼 클릭 즉시 발송 요청(POST 호출). 트리거 대기 없이 즉시 발송 가능.
  - 수신 주소를 GUI 설정에서 입력·저장. 알림메일 시트에 수신주소 열 추가, GAS는 해당 열에서 주소 읽어 발송.
  - 보낼 내역이 있을 때만 메일 버튼을 파란색(활성)으로 표시, 없을 때는 회색(비활성).

- **제어 패널 UI 개선**
  - 버튼을 두 줄 배치(row1/row2)로 창 넘침 방지. 버튼 문구 간소화(사건 조회 로드, 모든 사건 메일 발송).
  - 버튼 높이·모서리 통일(BTN_H=34, ROW_H=40, corner_radius=6). 이메일 버튼 텍스트 갱신 시에도 높이 고정.
  - 설정 버튼 색상을 비활성 버튼과 구분되도록 진한 톤(SETTINGS_FG/SETTINGS_HOVER)으로 변경.

- **로깅 시스템 강화**
  - 실행마다 새 로그 파일 생성(`logs/app_YYYYMMDD_HHMMSS.log`). 10개 초과 시 오래된 파일 자동 삭제.
  - 과거 로그 뷰어에 "클립보드에 복사" 버튼 추가. 선택한 로그 파일 내용을 한 번에 복사 가능.

## Technical

- **config.py**: `APP_VERSION = "4.2.0"`. `NOTIFICATION_EMAIL_ADDRESS`, `NOTIFICATION_GAS_WEBAPP_URL` 등 알림메일 설정.
- **utils/email_manager.py**: `get_summary_html()` 시트별 그룹화·HTML 색상 적용. `add_new_update(sheet_name=)` 지원.
- **services/google_sheets.py**: `append_notification_mail(summary_html, recipient_email)` 4열(일시, 수신주소, 메일내용, 발송상태).
- **gui/panels/control_panel.py**: 2줄 레이아웃, 이메일 버튼 활성/비활성 색상, 설정 버튼 색상 상수.
- **services/logger_service.py**: 실행 시 `app_YYYYMMDD_HHMMSS.log` 생성, `_cleanup_old_logs()`로 최대 10개 유지.
- **gui/dialogs/log_viewer_dialog.py**: "클립보드에 복사" 버튼 및 `_copy_to_clipboard()`.
- **gas/SendNotificationMail.gs**: 수신주소를 시트 열에서 읽도록 변경. `doPost` 웹 앱 즉시 발송 지원.

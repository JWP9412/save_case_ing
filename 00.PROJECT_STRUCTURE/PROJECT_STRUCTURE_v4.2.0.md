# 프로젝트 구조 (Project Structure) - v4.2.0

## Root Directory
- **`batch_gui_maker.py`**:
  - 메인 GUI 로직. v4.2.0: 알림메일 수동 발송(`send_notification_email`), GAS 웹 앱 즉시 호출, 이메일 버튼 활성/비활성 갱신(`update_email_btn_text`).
  - v4.1.2: 사건 목록 UI 패널 위임. v4.1.0: 표준 로거·GUI 핸들러·`log_message` 위임. v4.0.0: 배너 PIL·크기 조정.
  - `services/puppeteer.py`, `services/google_sheets.py`, `services/logger_service.py`, `utils/email_manager` 사용.
- **`config.py`**:
  - 설정 상수. v4.2.0 기준 `APP_VERSION = "4.2.0"`. `NOTIFICATION_EMAIL_ADDRESS`, `NOTIFICATION_GAS_WEBAPP_URL`, `UNSENT_EMAILS_FILE`, `NOTIFICATION_WORKSHEET_NAME` 등. JSON 파일 경로는 `data/` 하위로 통일.
- **`data/`** (v4.2.0): 설정·이력용 JSON 통합 폴더. `user_settings.json`, `column_widths.json`, `column_order.json`, `right_panel_width.json`, `update_history.json`, `status_history.json`, `theme_config.json`, `unsent_emails.json`, `search_log.json`. `.gitignore`로 제외.
- **`maintenance.js`**: 유지보수 설정. `src/interactive_runner.js`, `src/single-case-captcha.js`에서 참조.
- **`main.py`**: 진입점. `config.load_user_settings()` 후 `gui.main_window.run_app()` 호출.
- **`requirements.txt`**, **`package.json`**: 의존성.
- **`logs/`**: v4.2.0. 실행마다 `app_YYYYMMDD_HHMMSS.log` 생성. 10개 초과 시 오래된 파일 자동 삭제. `logger_service`가 생성·정리.
- **`assets/`**: 헤더 배너 등. `config.HEADER_IMAGE_PATH`.

## src/ (Puppeteer Automation)
- **`interactive_runner.js`**: 단일 지속 프로세스. **`PageController.js`**: 대법원 DOM 상호작용. **`single-case-captcha.js`**: 캡차 캡처.
- **`maintenance.js`**: `browserHeadless` 등.

## services/ (Python Modules)
- **`logger_service.py`** (v4.2.0):
  - 실행 시 `app_YYYYMMDD_HHMMSS.log` 파일 핸들러 등록. `_cleanup_old_logs()`로 최대 10개 유지.
  - `get_available_log_paths()`, `GuiLogHandler`, `register_gui_handler()`, `get_logger()`.
- **`puppeteer.py`**: Node.js 프로세스 생성·관리.
- **`google_sheets.py`** (v4.2.0): `append_notification_mail(summary_html, recipient_email)` 4열(일시, 수신주소, 메일내용, 발송상태).
- **`update_history.py`**: 로컬 업데이트 기록.

## gui/
- **`main_window.py`**: 창 조립. `run_app()`에서 패널 배치 후 `run()`.
- **`panels/`** (v4.2.0):
  - **ControlPanel**: 버튼 2줄(row1/row2), 높이·corner_radius 통일. 이메일 버튼 활성 시에만 파란색. 설정 버튼 진한 색(SETTINGS_FG).
  - **CaseListPanel**: 사건 목록(N), 가로 스크롤. **HeaderPanel**, **SettingsPanel**, **ProgressPanel**.
- **`dialogs/`** (v4.2.0):
  - **log_viewer_dialog.py**: 과거 로그 파일 선택·표시, "클립보드에 복사" 버튼, 새로고침, 폴더 열기.
  - **settings_dialog.py**: GOOGLE_SHEET_ID, NOTIFICATION_EMAIL_ADDRESS, NOTIFICATION_GAS_WEBAPP_URL 등 편집.
- **`captcha_dialog.py`**: 캡차 입력 팝업.

## utils/ (v4.1.2, v4.2.0)
- **`email_manager.py`** (v4.2.0): `load_unsent_emails`, `save_unsent_emails`, `add_new_update(case_number, updates, sheet_name=)`, `get_summary_html()` 시트별 그룹화·HTML 색상, `get_summary_text`, `clear_unsent_emails_and_update_last_sent`.
- `__init__.py`로 패키지 등록.

## gas/
- **`SendNotificationMail.gs`** (v4.2.0): 알림메일 시트에서 '대기' 행 읽어 수신주소(2열)·메일내용(3열) 사용해 발송. `doPost` 웹 앱 즉시 발송. **`README.md`**: 웹 앱 배포·URL 설정 안내.

## api/certification/
- 구글 API 서비스 계정. `service-account.json`은 `.gitignore` 대상.

## 기타 디렉토리
- **`cookie_data_for_save/instance_N`**: 브라우저 사용자 데이터.
- **`screenshots/`**: 캡차 이미지. **`results/`**: 크롤링 결과 JSON.
- **`00.CHANGELOG/`**, **`00.README/`**, **`00.PROJECT_STRUCTURE/`**: 버전별 문서.

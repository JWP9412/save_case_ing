# 프로젝트 구조 (Project Structure) - v4.3.99

## Root Directory
- **`config.py`** (v4.3.99): 버전 상수 `APP_VERSION = "4.3.99"` 설정.
- **`main.py`**: `--auto` 파라미터 처리 및 `run_auto_batch` 호출 분기. GUI 모드는 `gui.main_window.run_app()` 진입.
- **`auto_runner.py`**: CLI 전용 실행기. `MockApp`이 ProcessController와 동일한 인터페이스(show_warning, show_info, ask_yesno, get_case_status_text 등) 제공.
- **`data/`**: 설정 및 이력용 JSON 통합 폴더.
- **`logs/`**: 실행 시마다 새 로그 파일 생성 (최대 10개 유지).

## gui/ (UI)
- **`main_window.py`**: GUI 조립 및 실행. `AppController` 인스턴스 생성 및 `run()` 호출.
- **`app_controller.py`**: 메인 컨트롤러. ProcessController, 패널, 유틸 위임 및 이벤트 조정.
- **`panels/`**: ControlPanel, CaseListPanel, HeaderPanel 등 UI 컴포넌트.
- **`dialogs/`**: captcha_dialog, settings_dialog, find_dialog, sheet_viewer_dialog 등.
- **`utils/`**: UI 전용 헬퍼.
  - `ui_queue_manager.py`: 비동기 UI 큐 처리, 상태/진행률 갱신.
  - `case_list_builder.py`, `history_ui.py`, `column_resizer.py`: 사건 목록·타임스탬프·컬럼 리사이즈.
  - `google_sheet_ui.py`: 구글 시트 로드 후 UI 갱신 위임.
  - `search_ui.py`, `selection_manager.py`, `email_ui.py`, `captcha_ui.py`: 검색/선택/이메일/캡차 UI.
  - `window_lifecycle.py`, `window_bootstrap.py`, `bind_utils.py`, `case_list_columns.py`.

## services/ (Business Logic)
- **`process_controller.py`**: 사건 처리·캡차·병렬 실행. app 위임으로 UI 결합 최소화.
- **`google_sheets.py`**: 시트 읽기/쓰기, 진행내용 저장, 알림메일 시트 기록.
- **`email_manager.py`**: 미발송 이메일 내역(unsent_emails.json), 요약 HTML/푸터 생성. (기존 utils에서 이동)
- **`history_manager.py`**: 검색 로그·상태 히스토리 파일 I/O.
- **`update_history.py`**: 사건별 마지막 업데이트 일시·행 개수(update_history.json).
- **`puppeteer.py`**: Node.js 프로세스·Puppeteer IPC.
- **`logger_service.py`**, **`search_manager.py`**, **`sort_manager.py`**, **`theme_manager.py`**: 로깅, 검색, 정렬, 테마.

## src/ (Puppeteer Automation)
- **`interactive_runner.js`**, **`PageController.js`**: Puppeteer 실행 및 DOM 제어.

## gas/ (Google Apps Script)
- **`SendNotificationMail.gs`**: 즉시 발송용 웹 앱 스크립트.

## 문서
- **`00.CHANGELOG/`**, **`00.README/`**, **`00.PROJECT_STRUCTURE/`**: 버전별 변경 이력 및 구조 문서.
- **`utils/` 폴더는 v4.3.99에서 제거됨.** 이메일 로직은 `services/email_manager.py`로 통합.

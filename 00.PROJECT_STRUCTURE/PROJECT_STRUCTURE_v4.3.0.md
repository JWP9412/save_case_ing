# 프로젝트 구조 (Project Structure) - v4.3.0

## Root Directory
- **`batch_gui_maker.py`**: 메인 GUI. v4.2.2의 리팩터링 구조를 유지하며, 이메일 버튼 활성화 및 결과 요약 데이터 전달 연동.
- **`config.py`** (v4.3.0 업데이트): 버전 상수 `APP_VERSION = "4.3.0"` 설정.
- **`main.py`**: `--auto` 파라미터 처리 및 `run_auto_batch` 호출 분기 포함.
- **`auto_runner.py`** (v4.3.0 강화):
  - CLI 전용 실행기. `MockApp` 클래스에 `profile_locks` 추가로 다중 접속 안전성 확보.
  - `process_worker` 내에서 브라우저 기동 단계(`process_cli_auto_case`)를 포함한 2단계 실행 구조 정립.
  - 이메일 요약용 결과를 딕셔너리 리스트(`{"사건번호", "피고", "사건명"}`) 형태로 수집 및 전달.
- **`data/`**: 설정 및 이력용 JSON 통합 폴더 (사용자 설정, 열 너비, 검색 로그 등).
- **`logs/`**: 실행 시마다 새 로그 파일 생성 (최대 10개 유지).

## src/ (Puppeteer Automation)
- **`interactive_runner.js`**: 단일 지속 프로세스 기반 Puppeteer 실행기.
- **`PageController.js`**: 대법원 사이트 DOM 제어 및 크롤링 핵심 로직.

## services/ (Python Business Logic)
- **`process_controller.py`** (v4.3.0 강화):
  - CLI 전용 자동 처리 메서드 `process_cli_auto_case` 추가. (브라우저 기동 후 클릭 명령 전송)
  - 이메일 요약용 결과 저장 메서드(`_save_run_result_for_email`)에서 딕셔너리 리스트 구조 지원.
- **`history_manager.py`**: 검색 로그 및 상태 히스토리 파일 I/O 전담.
- **`puppeteer.py`**: Node.js 프로세스와의 IPC 통신 및 라이프사이클 관리.
- **`google_sheets.py`**: gspread를 이용한 시트 읽기/쓰기 및 알림메일 데이터 기록.

## gui/ (UI Components)
- **`panels/`**: `ControlPanel`, `CaseListPanel` 등 UI 컴포넌트 분리 관리.
- **`dialogs/`**: `log_viewer_dialog.py`, `settings_dialog.py`, `captcha_dialog.py`.

## utils/ (Utility Modules)
- **`email_manager.py`** (v4.3.0 강화):
  - 딕셔너리 리스트 형식의 요약 결과 캐시(`_last_run_result_cache`) 지원.
  - `_build_run_result_footer`: 수집된 사건들을 **[사건번호 | 피고/사건명]** 컬럼의 HTML 테이블로 렌더링하는 전용 로직 포함.

## gas/ (Google Apps Script)
- **`SendNotificationMail.gs`**: 즉시 발송을 위한 `doPost` 웹 앱 스크립트.

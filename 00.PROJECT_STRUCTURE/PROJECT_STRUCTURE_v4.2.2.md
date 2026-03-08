# 프로젝트 구조 (Project Structure) - v4.2.2

## Root Directory
- **`batch_gui_maker.py`** (v4.2.2 업데이트):
  - 메인 GUI (UI 구성 및 이벤트 처리).
  - 비대해진 사건 처리 및 데이터 관리 로직을 서비스 모듈(`ProcessController`, `HistoryManager`)로 대폭 위임.
  - UI 일관성을 위해 제어 패널 버튼 높이/크기 통일 로직 포함.
- **`config.py`**:
  - 설정 상수. v4.2.2 기준 `APP_VERSION = "4.2.2"`.
- **`main.py`**: 진입점.
- **`package.json`**: v4.2.2에서 Cypress 관련 내용 제거 및 Node.js 패키지 명세 최적화.
- **`data/`**: 설정 및 이력용 JSON 통합 폴더 (사용자 설정, 열 너비, 검색 로그 등).
- **`logs/`**: 실행 시마다 새 로그 파일 생성 (최대 10개 유지).

## src/ (Puppeteer Automation)
- **`interactive_runner.js`**: 단일 지속 프로세스 기반 Puppeteer 실행기.
- **`PageController.js`**: 대법원 사이트 DOM 제어 및 크롤링 핵심 로직.
- **`maintenance.js`**: 브라우저 헤드리스 여부 등 유지보수 설정.

## services/ (Python Business Logic) - v4.2.2 핵심 강화
- **`process_controller.py`** (v4.2.2 신규):
  - `batch_gui_maker.py`에서 분리된 핵심 비즈니스 로직 담당.
  - 병렬 처리 관리, 캡차 처리 프로세스, 구글 시트 저장 흐름 제어.
- **`history_manager.py`** (v4.2.2 신규):
  - 검색 로그(`search_log.json`) 및 상태 히스토리(`status_history.json`) 파일 I/O 전담.
- **`logger_service.py`**: 실행별 로그 파일 생성 및 자동 삭제 로직.
- **`puppeteer.py`**: Node.js 프로세스와의 IPC 통신 및 라이프사이클 관리.
- **`google_sheets.py`**: gspread를 이용한 시트 읽기/쓰기 및 알림메일 데이터 기록.
- **`update_history.py`**: 증분 업데이트를 위한 마지막 저장 항목 기록 관리.

## gui/ (UI Components)
- **`main_window.py`**: 전체 창 구성 및 레이아웃 조립.
- **`panels/`**:
  - **ControlPanel**: 2줄 버튼 배치, 버튼 높이(34px) 및 스타일 통일. 이메일 상태별 색상 제어.
  - **CaseListPanel**: 사건 목록 표시 및 열 너비 조정 기능.
  - **ProgressPanel**, **HeaderPanel**, **SettingsPanel**.
- **`dialogs/`**:
  - **log_viewer_dialog.py**: 과거 로그 조회 및 클립보드 복사.
  - **settings_dialog.py**: 앱 주요 설정 편집.
  - **captcha_dialog.py**: 캡차 입력 팝업 UI.

## utils/ (Utility Modules)
- **`email_manager.py`**: 미발송 메일 관리, HTML 요약 생성, GAS 연동 처리.

## gas/ (Google Apps Script)
- **`SendNotificationMail.gs`**: 즉시 발송을 위한 `doPost` 웹 앱 스크립트.

## api/certification/
- 구글 클라우드 서비스 계정 인증 파일 (`service-account.json`).

## Documentation & Assets
- **`assets/`**: 로고 및 배너 이미지.
- **`00.CHANGELOG/`**, **`00.README/`**, **`00.PROJECT_STRUCTURE/`**: 버전별 상세 문서.

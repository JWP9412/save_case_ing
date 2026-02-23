# 프로젝트 구조 (Project Structure) - v4.1.2

## Root Directory
- **`batch_gui_maker.py`**:
  - 메인 GUI 로직. v4.1.2: 리팩토링으로 사건 목록 UI를 패널로 위임, 코드 경량화.
  - v4.1.0: 표준 로거 초기화(`setup_logger`), GUI 핸들러 등록(`register_gui_handler`), `log_message`가 로거로 위임.
  - v4.0.0: 배너 이미지 PIL 전달, 배너 크기 조정. v3.3.0: 열 너비 Excel 스타일 리사이즈, 열 너비 저장/복원.
  - `services/puppeteer.py`, `services/google_sheets.py`, `services/logger_service.py` 사용.
- **`config.py`**:
  - 설정 상수. v4.1.2 기준 `APP_VERSION = "4.1.2"`. `COLUMN_WIDTHS_FILE`, `HEADER_IMAGE_PATH`, `USER_SETTINGS_FILE` 등.
- **`maintenance.js`** (v3.3.0):
  - 유지보수 설정. `browserHeadless` 등. `src/interactive_runner.js`, `src/single-case-captcha.js`에서 참조.
- **`main.py`**: 진입점. `config.load_user_settings()` 후 `gui.main_window.run_app()` 호출.
- **`requirements.txt`**, **`package.json`**: 의존성.
- **`search_log.json`**, **`column_widths.json`** 등: 앱에서 참조하는 JSON 설정/이력. `.gitignore`에 일부 포함.
- **`logs/`**: v4.1.0. `app.log` 및 날짜별 순환 파일(`app.log.YYYY-MM-DD`). `logger_service`가 생성.
- **`assets/`**: 헤더 배너 등. `config.HEADER_IMAGE_PATH`로 지정.

## src/ (Puppeteer Automation)
- **`interactive_runner.js`**: 단일 지속 프로세스 모델. `maintenance.js`의 `browserHeadless` 사용.
- **`PageController.js`**: 대법원 사이트 DOM 상호작용.
- **`single-case-captcha.js`**: `maintenance.browserHeadless` 사용.
- **`index.js`**, **`BrowserManager.js`**, **`ParallelProcessor.js`**: 구버전/호환용.

## services/ (Python Modules)
- **`logger_service.py`** (v4.1.0):
  - 전역 로거(`case_ing`), `setup_logger()`, `TimedRotatingFileHandler`(logs/app.log), `GuiLogHandler`, `register_gui_handler()`, `get_logger()`, `get_available_log_paths()`.
- **`puppeteer.py`**: Node.js 프로세스(`interactive_runner.js`) 생성 및 관리. v4.1.0: 표준 로거 사용.
- **`google_sheets.py`**: gspread 구글 시트 연동. v4.1.0: 표준 로거 사용.
- **`update_history.py`**: 로컬 업데이트 기록 읽기/쓰기.

## gui/
- **`main_window.py`** (v4.1.0): 창 조립. `run_app()`에서 `BatchProcessingGUI` 생성, 헤더·PanedWindow(좌/우)·패널 배치 후 `run()`.
- **`panels/`** (v4.1.0, v4.1.2):
  - `HeaderPanel`, `ControlPanel`, `SettingsPanel`, `CaseListPanel`, `ProgressPanel`. 각각 `create(parent, app)` 스타일.
  - `CaseListPanel` (v4.1.2): 사건 목록 전담 패널로 정리. 제목 "사건 목록(N)", 가로 스크롤 동기화(`_sync_xview(*args)`).
  - `ProgressPanel`: 진행률 바, 로그 텍스트, 하단 "복사"/"과거 로그" 버튼.
- **`dialogs/`** (v4.1.0):
  - `settings_dialog.py`: 사용자 설정(GOOGLE_SHEET_ID 등) GUI 편집.
  - `log_viewer_dialog.py`: 과거 로그 파일 선택·내용 표시, 새로고침, 폴더 열기.
- **`captcha_dialog.py`**: 캡차 입력 팝업.

## utils/ (v4.1.2)
- 공통 유틸 모듈용 패키지. `__init__.py`로 패키지 등록. 향후 헬퍼 함수·공통 로직 배치.

## api/certification/
- 구글 API 인증 및 서비스 계정. `service-account.json`은 `.gitignore` 대상.

## 기타 디렉토리
- **`cookie_data_for_save/instance_N`**: 브라우저 사용자 데이터.
- **`screenshots/`**: 캡차 이미지 등.
- **`results/`**: 크롤링 결과 JSON 임시 저장.
- **`00.CHANGELOG/`**, **`00.PROJECT_STRUCTURE/`**, **`00.README/`**: 버전별 문서.

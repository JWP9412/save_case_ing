# 프로젝트 구조 (Project Structure) - v3.2.1

## Root Directory
- **`batch_gui_maker.py`**:
  - 프로젝트의 메인 GUI 프로그램입니다.
  - v3.2.1: `tk.BooleanVar` 초기화 시점 수정을 통해 런타임 오류가 해결되었으며, 버전/타이틀 정보를 `config.py`에서 중앙 집중식으로 관리합니다.
  - `services/puppeteer.py`를 통해 Node.js 프로세스를 제어하고, `services/google_sheets.py`를 통해 데이터를 저장합니다.
- **`config.py`**:
  - 설정 상수 모음. v3.2.1에서 앱 버전(`APP_VERSION`), 표시 타이틀(`APP_TITLE`), 부제목(`APP_SUBTITLE`) 설정이 추가되었습니다.
- **`main.py`**: 진입점(선택 사용).
- **`requirements.txt`**: Python 의존성 패키지 목록.
- **`package.json`**: Node.js 의존성 패키지 목록.
- **`search_log.json`**: 검색 성공 이력(사건번호 목록). '기록' 열 표시용. 쿠키 폴더 삭제 시 자동 초기화됩니다.

## src/ (Puppeteer Automation)
- **`interactive_runner.js`** (핵심):
  - 단일 지속 프로세스 모델의 핵심 엔진입니다.
  - Python에서 실행되며, 브라우저를 띄우고 명령(캡차 입력, 검색 등)을 대기합니다.
  - `cookie_data_for_save/instance_N` 폴더를 사용하여 전용 차로(인스턴스)별 세션을 유지합니다.
- **`PageController.js`**:
  - 대법원 사이트의 DOM 요소와 상호작용하는 모든 로직(입력, 클릭, 데이터 추출)을 담당합니다.
  - v3.2.1: 검색 결과 로딩 대기 로직이 강화되었으며, 진행내용 그리드 탐색 시 예비(fallback) 전략이 추가되었습니다.
- **`index.js`**, **`single-case-captcha.js`**, **`BrowserManager.js`**, **`ParallelProcessor.js`**:
  - 구버전/호환용 또는 특정 상황에서 참조됩니다.

## services/ (Python Modules)
- **`puppeteer.py`**:
  - Node.js 프로세스(`interactive_runner.js`)를 생성(Popen)하고 관리합니다.
- **`google_sheets.py`**:
  - gspread를 사용하여 구글 시트와 연동합니다. 사건 목록 로드 및 진행내용 저장.
- **`update_history.py`**:
  - 로컬 업데이트 기록(날짜, 행 개수 등) 읽기/쓰기.

## gui/
- **`captcha_dialog.py`**: 캡차 입력 팝업 등 GUI 컴포넌트.

## api/certification/
- 구글 API 인증 및 서비스 계정 설정.

## 기타 디렉토리
- **`cookie_data_for_save/instance_N`**: 브라우저 사용자 데이터(쿠키 등).
- **`screenshots/`**: 캡차 이미지 및 디버그 스크린샷.
- **`results/`**: 크롤링 결과 JSON 임시 저장.
- **`00.CHANGELOG/`**, **`00.PROJECT_STRUCTURE/`**, **`00.README/`**: 버전별 변경 이력 및 문서.

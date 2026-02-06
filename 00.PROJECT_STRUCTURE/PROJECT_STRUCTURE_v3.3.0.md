# 프로젝트 구조 (Project Structure) - v3.3.0

## Root Directory
- **`batch_gui_maker.py`**:
  - 프로젝트의 메인 GUI 프로그램입니다.
  - v3.3.0: 사건 목록 열 너비 Excel 스타일 리사이즈(가이드라인, 리빌드 없이 적용), 열 너비 저장/복원(`column_widths.json`), 캡차 입력란 Backspace/Delete 허용.
  - `services/puppeteer.py`를 통해 Node.js 프로세스를 제어하고, `services/google_sheets.py`를 통해 데이터를 저장합니다.
- **`config.py`**:
  - 설정 상수 모음. v3.3.0에서 `COLUMN_WIDTHS_FILE`(열 너비 저장 파일명)이 추가되었습니다.
- **`maintenance.js`** (v3.3.0 신규):
  - 유지보수용 설정. `browserHeadless` 등 브라우저 표시 여부를 한 곳에서 관리하며, `src/interactive_runner.js`, `src/single-case-captcha.js`에서 참조합니다.
- **`main.py`**: 진입점(선택 사용).
- **`requirements.txt`**: Python 의존성 패키지 목록.
- **`package.json`**: Node.js 의존성 패키지 목록.
- **`search_log.json`**: 검색 성공 이력(사건번호 목록). '기록' 열 표시용.
- **`column_widths.json`** (v3.3.0): 사용자가 조절한 사건 목록 열 너비 저장. 앱 실행 시 자동 로드.

## src/ (Puppeteer Automation)
- **`interactive_runner.js`** (핵심):
  - 단일 지속 프로세스 모델의 핵심 엔진입니다.
  - v3.3.0: `maintenance.js`의 `browserHeadless`를 사용하여 기본적으로 브라우저 창을 숨깁니다.
  - `cookie_data_for_save/instance_N` 폴더를 사용하여 전용 차로(인스턴스)별 세션을 유지합니다.
- **`PageController.js`**: 대법원 사이트 DOM 상호작용(입력, 클릭, 데이터 추출).
- **`single-case-captcha.js`**: v3.3.0에서 `maintenance.browserHeadless` 사용.
- **`index.js`**, **`BrowserManager.js`**, **`ParallelProcessor.js`**: 구버전/호환용 또는 특정 상황에서 참조됩니다.

## services/ (Python Modules)
- **`puppeteer.py`**: Node.js 프로세스(`interactive_runner.js`) 생성 및 관리.
- **`google_sheets.py`**: gspread로 구글 시트 연동. 사건 목록 로드 및 진행내용 저장.
- **`update_history.py`**: 로컬 업데이트 기록(날짜, 행 개수 등) 읽기/쓰기.

## gui/
- **`captcha_dialog.py`**: 캡차 입력 팝업 등 GUI 컴포넌트.

## api/certification/
- 구글 API 인증 및 서비스 계정 설정.

## 기타 디렉토리
- **`cookie_data_for_save/instance_N`**: 브라우저 사용자 데이터(쿠키 등).
- **`screenshots/`**: 캡차 이미지 및 디버그 스크린샷.
- **`results/`**: 크롤링 결과 JSON 임시 저장.
- **`00.CHANGELOG/`**, **`00.PROJECT_STRUCTURE/`**, **`00.README/`**: 버전별 변경 이력 및 문서.

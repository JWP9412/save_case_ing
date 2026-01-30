# 프로젝트 구조 (Project Structure)

## 📂 Root Directory
- **`batch_gui_maker.py`**: 
  - 프로젝트의 메인 진입점입니다. 
  - Tkinter 기반의 GUI를 생성하고 사용자와 상호작용합니다.
  - `services/puppeteer.py`를 통해 Node.js 프로세스를 제어하고, `services/google_sheets.py`를 통해 데이터를 저장합니다.
- **`gui_maker.py`**: 
  - 레거시 GUI 컴포넌트 또는 캡차 입력 전용 팝업 창을 관리합니다.
- **`requirements.txt`**: Python 의존성 패키지 목록입니다.
- **`package.json`**: Node.js 의존성 패키지 목록입니다.

## 📂 src/ (Puppeteer Automation)
- **`interactive_runner.js`** (핵심): 
  - **단일 지속 프로세스** 모델의 핵심 엔진입니다.
  - Python에서 실행되며, 브라우저를 띄우고 명령(캡차 입력, 검색 등)을 대기합니다.
  - 브라우저 세션을 유지하여 캡차 변경이나 쿠키 소실을 방지합니다.
- **`PageController.js`**: 
  - 대법원 사이트의 DOM 요소와 상호작용하는 모든 로직이 담겨 있습니다.
  - 입력(사건번호, 당사자명), 클릭(검색, 탭), 데이터 추출(진행내용 그리드) 등을 담당합니다.
- **`index.js` & `single-case-captcha.js`**: 
  - 구버전 아키텍처에서 사용하던 파일들로, 현재는 호환성을 위해 유지되거나 특정 상황에서 참조됩니다.

## 📂 services/ (Python Modules)
- **`puppeteer.py`**: 
  - Node.js 프로세스(`interactive_runner.js`)를 생성(Popen)하고 관리합니다.
  - 표준 입출력(stdin/stdout)을 통해 명령을 보내고 결과를 수신합니다.
- **`google_sheets.py`**: 
  - gspread 라이브러리를 사용하여 구글 시트와 연동합니다.
  - 사건 목록을 읽어오고, 크롤링된 진행내용을 저장합니다.

## 📂 기타 디렉토리
- **`screenshots/`**: 캡처된 캡차 이미지나 디버그용 스크린샷이 저장됩니다.
- **`results/`**: 크롤링 결과 데이터가 JSON 형태로 임시 저장됩니다.
- **`user_data/`**: 브라우저 쿠키 및 세션 데이터가 저장되어 재실행 시에도 로그인이 유지되도록 합니다.

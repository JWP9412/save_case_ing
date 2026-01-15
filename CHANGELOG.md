# 📝 변경 이력 (Changelog)

이 파일은 프로젝트의 모든 주요 변경사항을 기록합니다.

형식은 [Keep a Changelog](https://keepachangelog.com/ko/1.0.0/)를 따르며,
버전 관리는 [Semantic Versioning](https://semver.org/lang/ko/)을 따릅니다.

---

## [3.0.0] - 2025-11-13

### ✨ 추가됨 (Added)

#### Python GUI 일괄 처리 시스템
- **메인 GUI 프로그램** (`batch_gui_maker.py`)
  - 구글 시트 자동 로드 기능
  - 사건 목록 체크박스 선택
  - 병렬 처리 설정 (1~10개)
  - 캡차 이미지 자동 캡처 및 표시
  - 캡차 수동 입력 (Enter 키로 다음 입력칸 이동)
  - 실시간 진행상황 로그
  - 업데이트 일시 및 경과일 표시 (D+n 형식)

#### GUI 컴포넌트
- **CaptchaGUI 클래스** (`gui_maker.py`)
  - 캡차 이미지 표시
  - 입력창 생성
  - 레이아웃 관리

#### 구글 시트 연동 개선
- **워크시트 자동 생성**: `{피고}_{비고}_{사건번호}_{법원}` 형식
- **업데이트 일시 기록**: 현재 및 이전 업데이트 시간 저장
- **로컬 업데이트 기록**: `update_history.json`에 로컬 저장
- **자동 시트 초기화**: 이전 데이터 삭제 후 새 데이터 저장

#### Puppeteer 스크립트 개선
- **브라우저 재연결**: WebSocket URL로 기존 브라우저 재사용
- **진행내용 탭 자동 클릭**: 진행내용 데이터 자동 추출
- **그리드 데이터 파싱**: JavaScript로 DOM에서 직접 데이터 추출
- **자동 브라우저 종료**: 처리 완료 후 자동 종료

#### 사용자 경험 개선
- **고정 헤더**: 스크롤 시에도 헤더 고정
- **번갈아가는 행 배경색**: 가독성 향상
- **상태 이모지**: 처리 상태 시각화 (⏳/🔄/✅/❌)
- **실시간 로그**: 처리 과정 상세 로그
- **디버그 로그**: 문제 해결용 상세 정보

### 🔧 변경됨 (Changed)

#### 프레임워크 전환
- **Cypress → Puppeteer**: 완전 마이그레이션
  - 다중 브라우저 인스턴스 관리
  - 빠른 처리 속도
  - 더 나은 안정성

#### 파일 구조 정리
- Cypress 관련 파일 완전 제거
- 불필요한 Python 스크립트 제거
- 백업 파일 제거
- 임시 데이터 파일 제거

#### 사용자 인터페이스
- 단일 창 GUI로 통합 (여러 창 → 하나의 통합 GUI)
- 모든 기능을 하나의 화면에서 처리
- 더 직관적인 워크플로우

### 🗑️ 제거됨 (Removed)

#### Cypress 관련 (완전 제거)
- `cypress/` 폴더 전체
- `cypress.config.js`
- `cypress.env.json`
- `create-fixtures-python.py`

#### 사용되지 않는 Python 스크립트
- `button_handler.py`
- `captcha_input.py`
- `captcha_input_backup.py`
- `image_finder.py`
- `fix_move_to_next.py`
- `test_batch_system.py`
- `progress-extractor.py`
- `puppeteer-to-sheets.py`
- `excel-based-sheets.py`
- `create-new-spreadsheet.py`

#### Node.js 스크립트
- `src/close-browser.js` (사용 안 함)

#### 임시 파일
- `progress_data_*.json` (3개 파일)
- `yarn.lock` (npm 사용)
- `puppeteer-package.json` (중복)

#### 문서
- `puppeteer-migration-plan.md` (마이그레이션 완료)

### 🐛 수정됨 (Fixed)

- **브라우저 종료 문제**: 처리 완료 후 자동 종료 로직 추가
- **캡차 이미지 표시**: GUI에서 이미지 정상 표시
- **구글 시트 저장**: 안정적인 저장 로직
- **병렬 처리**: ThreadPoolExecutor로 안정적인 병렬 처리
- **한글 인코딩**: Windows 환경에서 한글 정상 표시
- **Enter 키 동작**: 다음 입력칸으로 정확한 이동

### 📁 파일 구조 변경

#### 이름 변경
- `api/certification/README.md` → `api/certification/GOOGLE_AUTH_SETUP.md`

#### 새로 추가
- `CHANGELOG.md` (이 파일)
- `update_history.json` (로컬 업데이트 기록)

---

## [2.2.0] - 2025년 9월 (추정)

### ✨ 추가됨
- Puppeteer 마이그레이션 완료
- 구글 시트 연동
- 워크시트 이름 자동 생성
- 캡차 처리 개선

### 🔧 변경됨
- Cypress → Puppeteer 전환
- 입력 속도 최적화 (JavaScript DOM 조작)
- WebSquare 프레임워크 호환성 개선

### 📁 새로운 파일
- `src/BrowserManager.js`
- `src/PageController.js`
- `src/ParallelProcessor.js`
- `src/index.js`

---

## [2.1.0] - 2025년 7월(추정)

### ✨ 추가됨
- 실시간 대화형 캡차 처리 시스템
- Python Tkinter GUI 입력창
- 모듈화된 파일 구조

### 🐛 수정됨
- 체크박스 체크 문제 해결
- 사건번호 입력 필드 오류 해결
- 파이썬 GUI 열리지 않는 문제 해결
- Windows 이모지 인코딩 오류 해결

### 📁 새로운 파일
- `captcha_input.py`
- `image_finder.py`
- `gui_maker.py`
- `button_handler.py`

---

## [1.x] - 원본 프로젝트

### ✨ 주요 기능
- Cypress 기반 자동화
- OCR 캡차 인식
- 구글 스프레드시트 연동
- AWS Lambda 서버리스 백엔드
- S3 스크린샷 저장

### 기술 스택
- Cypress (크롤링)
- Scikit-learn (캡차 학습)
- Serverless Framework (API)
- Python Tkinter (GUI)

---

## 📌 변경 유형 설명

- **추가됨 (Added)**: 새로운 기능
- **변경됨 (Changed)**: 기존 기능의 변경
- **제거됨 (Removed)**: 삭제된 기능
- **수정됨 (Fixed)**: 버그 수정
- **보안 (Security)**: 보안 관련 변경
- **성능 (Performance)**: 성능 개선

---

## 📝 버전 번호 규칙

- **Major (X.0.0)**: 호환되지 않는 API 변경
- **Minor (0.X.0)**: 하위 호환되는 기능 추가
- **Patch (0.0.X)**: 하위 호환되는 버그 수정

---

## 🔗 관련 링크

- **GitHub 저장소**: https://github.com/JWP9412/save_case_ing
- **원본 프로젝트**: https://github.com/iicdii/case-ing
- **이슈 트래커**: https://github.com/JWP9412/save_case_ing/issues

---

*최종 업데이트: 2025-11-13*


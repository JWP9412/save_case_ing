# case-ing

대법원 나의 사건 조회 자동화 시스템 (Puppeteer + Python GUI) - v4.1.2

## 원본 출처

이 프로젝트는 [iicdii/case-ing](https://github.com/iicdii/case-ing)를 기반으로 하여 **Puppeteer 기반 병렬 처리** 및 **Python GUI 일괄 처리 시스템**으로 전환한 포크 버전입니다.

**원본 저장소**: https://github.com/iicdii/case-ing  
**포크 저장소**: https://github.com/JWP9412/save_case_ing

<a href="https://github.com/iicdii/case-ing/blob/master/LICENSE" alt="License">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg" />
</a>

case-ing는 case + ~ing의 합성어로 여러 개의 사건 진행현황을 쉽게 조회하도록 도와주는 자동화 도구입니다.

---

## 현재 버전 특징 (v4.1.2)

### 주요 개선 사항

1. **리팩토링 및 구조 정리** *(v4.1.2 신규)*
   - 사건 목록 UI를 `gui/panels/case_list_panel.py`로 분리. 메인 GUI 로직 경량화.
   - `utils/` 폴더 추가(공통 유틸 모듈용). 백업 파일(`batch_gui_maker_v2_backup.py`) 제거.

2. **표준 로깅 및 로그 뷰어** *(v4.1.0)*
   - `logs/app.log`에 날짜별 순환 저장. 진행상황 패널과 동기화되는 GUI 로그 핸들러.
   - 진행상황 하단 "복사" 버튼으로 로그 전체 클립보드 복사, "과거 로그" 버튼으로 이전 로그 파일 조회.

3. **사건 목록 UI 개선** *(v4.1.0)*
   - 제목에 현재 사건 개수 표시: "사건 목록(N)".
   - 사건 목록 가로 스크롤바 정상 작동 수정.

4. **배너 이미지 표시 및 크기 최적화** *(v4.0.0)*
   - 상단 배너 이미지가 CustomTkinter 요구사항(PIL Image 객체)에 맞게 정상 표시.
   - 배너 영역 높이(120px)에 맞춰 이미지 크기, 가로 최대 900px.

5. **사건 목록 열 너비 UX (Excel 스타일)** *(v3.3.0)*
   - 드래그 중 가이드라인만 표시, 열 너비는 `column_widths.json`에 저장·복원.

### 기존 주요 기능 (v3.2.x 이전)
- **스마트 병렬 처리**: 사건 수에 비례하여 병렬 처리 수 자동 계산 및 인스턴스 확장
- **대화형 러너**: 단일 지속 프로세스 모델로 캡차 이미지 유지 및 소켓 연결 안정성 확보
- **스마트 스킵**: 최근 검색 기록 활용 및 'CLICK' 입력 지원

---

## 프로젝트 구조

```
case-ing/
├── batch_gui_maker.py           메인 GUI 로직
├── config.py                    설정 상수 (APP_VERSION = "4.1.2" 등)
├── maintenance.js                유지보수 설정 (브라우저 표시 여부)
├── main.py                      진입점 (run_app 호출)
├── package.json                 Node.js 패키지
├── requirements.txt             Python 패키지
├── logs/                        로그 파일 (app.log, app.log.YYYY-MM-DD)
│
├── src/                         Puppeteer 자동화 코드
│   ├── interactive_runner.js    대화형 Puppeteer 실행
│   ├── PageController.js        페이지 자동화 로직
│   └── single-case-captcha.js   단일 캡차 캡처
│
├── services/                    Python 서비스 모듈
│   ├── logger_service.py       전역 로거, 파일/GUI 핸들러, 과거 로그 목록
│   ├── puppeteer.py             Node.js 프로세스 통신 및 제어
│   ├── google_sheets.py        구글 시트 연동
│   └── update_history.py       로컬 업데이트 기록
│
├── gui/                         GUI 컴포넌트
│   ├── main_window.py          창 조립 및 run_app()
│   ├── panels/                 헤더, 제어, 설정, 사건 목록, 진행상황 패널
│   ├── dialogs/                 설정, 과거 로그 뷰어 등 다이얼로그
│   └── captcha_dialog.py        캡차 입력 팝업
│
├── utils/                       공통 유틸 모듈 (v4.1.2)
├── api/certification/           구글 API 인증
├── assets/                      배너 등 에셋
├── screenshots/                 캡차 이미지 저장소
└── 00.CHANGELOG, 00.README, 00.PROJECT_STRUCTURE   버전별 문서
```

---

## 빠른 시작

### 1. 사전 준비
- **Node.js** >= 14, **Python** >= 3.7
- 의존성 설치: `npm install`, `pip install -r requirements.txt`

### 2. 구글 시트 설정
- 서비스 계정 설정 및 `api/certification/service-account.json` 저장
- `config.py` 또는 설정 다이얼로그에서 `GOOGLE_SHEET_ID` 설정

### 3. 프로그램 실행
```bash
python main.py
```
또는 `python batch_gui_maker.py` (레거시 진입점).

---

## 개발 히스토리

- **v4.1.2**: 리팩토링(사건 목록 UI 분리), utils 폴더 추가, 백업 파일 제거
- **v4.1.0**: 표준 로깅, 로그 복사/과거 로그 뷰어, 사건 목록(N), 가로 스크롤바 수정
- **v4.0.0**: 배너 이미지 PIL 전달 및 배너 높이에 맞춘 크기 최적화
- **v3.3.0**: 열 너비 Excel 스타일 UX, 열 너비 저장/복원, 캡차 삭제 허용
- **v3.2.1**: 런타임 오류 수정, 버전 관리 일원화
- **v3.2.0**: 스마트 병렬 처리, 쿠키·검색 기록 동기화
- **v3.1.0**: 대화형 러너, 스마트 스킵
- **v3.0.0**: Puppeteer 기반 Python GUI 일괄 처리

자세한 내역: `00.CHANGELOG/CHANGELOG_v4.1.2.md`

---

## 라이선스

MIT License

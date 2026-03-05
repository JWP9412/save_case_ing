# case-ing

대법원 나의 사건 조회 자동화 시스템 (Puppeteer + Python GUI) - v4.2.0

## 원본 출처

이 프로젝트는 [iicdii/case-ing](https://github.com/iicdii/case-ing)를 기반으로 하여 **Puppeteer 기반 병렬 처리** 및 **Python GUI 일괄 처리 시스템**으로 전환한 포크 버전입니다.

**원본 저장소**: https://github.com/iicdii/case-ing  
**포크 저장소**: https://github.com/JWP9412/save_case_ing

<a href="https://github.com/iicdii/case-ing/blob/master/LICENSE" alt="License">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg" />
</a>

case-ing는 case + ~ing의 합성어로 여러 개의 사건 진행현황을 쉽게 조회하도록 도와주는 자동화 도구입니다.

---

## 현재 버전 특징 (v4.2.0)

### 주요 개선 사항

1. **알림메일 고도화** *(v4.2.0 신규)*
   - 수동 발송: 제어 패널 "모든 사건 메일 발송" 버튼으로 미발송 내역을 구글 시트 '알림메일' 시트에 기록 후 GAS로 발송.
   - 메일 본문 HTML 표에 구글 시트 색상 반영. 시트(피고·사건명)별로 단락 구분.
   - 설정에서 수신 메일 주소·GAS 웹 앱 URL 입력. 웹 앱 URL 설정 시 버튼 클릭 즉시 발송 요청.

2. **제어 패널 UI 개선** *(v4.2.0)*
   - 버튼 2줄 배치, 문구 간소화. 버튼 높이·모서리 통일. 설정 버튼은 비활성과 구분되는 진한 색.
   - 메일 버튼은 보낼 내역이 있을 때만 파란색(활성), 없으면 회색(비활성).

3. **로깅 시스템 강화** *(v4.2.0)*
   - 실행마다 새 로그 파일(`logs/app_YYYYMMDD_HHMMSS.log`). 10개 초과 시 오래된 파일 자동 삭제.
   - 과거 로그 뷰어에 "클립보드에 복사" 버튼 추가.

4. **리팩토링 및 구조 정리** *(v4.1.2)*
   - 사건 목록 UI를 `gui/panels/case_list_panel.py`로 분리. `utils/` 폴더 추가.

5. **표준 로깅 및 로그 뷰어** *(v4.1.0)*
   - 진행상황 패널과 동기화되는 GUI 로그 핸들러. "복사"/"과거 로그" 버튼.

6. **사건 목록 UI 개선** *(v4.1.0)*
   - 제목 "사건 목록(N)", 가로 스크롤바 수정.

7. **배너 이미지 표시 및 크기 최적화** *(v4.0.0)*
   - CustomTkinter PIL 전달, 배너 높이 120px·가로 최대 900px.

8. **사건 목록 열 너비 UX (Excel 스타일)** *(v3.3.0)*
   - 열 너비 드래그·저장·복원.

### 기존 주요 기능 (v3.2.x 이전)
- **스마트 병렬 처리**: 사건 수에 비례 병렬 처리·인스턴스 확장
- **대화형 러너**: 단일 지속 프로세스, 캡차 이미지 유지·소켓 안정성
- **스마트 스킵**: 최근 검색 기록·CLICK 입력 지원

---

## 프로젝트 구조

```
case-ing/
├── batch_gui_maker.py           메인 GUI 로직
├── config.py                    설정 상수 (APP_VERSION = "4.2.0" 등)
├── maintenance.js                유지보수 설정 (브라우저 표시 여부)
├── main.py                      진입점 (run_app 호출)
├── package.json                 Node.js 패키지
├── requirements.txt             Python 패키지
├── logs/                        로그 파일 (app_YYYYMMDD_HHMMSS.log, 최대 10개)
│
├── src/                         Puppeteer 자동화 코드
│   ├── interactive_runner.js    대화형 Puppeteer 실행
│   ├── PageController.js        페이지 자동화 로직
│   └── single-case-captcha.js   단일 캡차 캡처
│
├── services/                    Python 서비스 모듈
│   ├── logger_service.py       전역 로거, 실행별 파일·과거 로그 목록
│   ├── puppeteer.py             Node.js 프로세스 통신 및 제어
│   ├── google_sheets.py        구글 시트 연동, 알림메일 시트 4열
│   └── update_history.py       로컬 업데이트 기록
│
├── gui/                         GUI 컴포넌트
│   ├── main_window.py          창 조립 및 run_app()
│   ├── panels/                 헤더, 제어(2줄 버튼), 설정, 사건 목록, 진행상황
│   ├── dialogs/                 설정, 과거 로그 뷰어(복사 버튼)
│   └── captcha_dialog.py        캡차 입력 팝업
│
├── utils/                       공통 유틸 (email_manager 등)
├── gas/                         GAS 스크립트 (SendNotificationMail.gs 웹 앱)
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

- **v4.2.0**: 알림메일 고도화(HTML·그룹화·즉시 발송), 제어 패널 UI·로깅 강화
- **v4.1.2**: 리팩토링(사건 목록 UI 분리), utils 폴더 추가
- **v4.1.0**: 표준 로깅, 로그 복사/과거 로그 뷰어, 사건 목록(N), 가로 스크롤바 수정
- **v4.0.0**: 배너 이미지 PIL 전달 및 배너 높이에 맞춘 크기 최적화
- **v3.3.0**: 열 너비 Excel 스타일 UX, 열 너비 저장/복원
- **v3.2.x ~ v3.0.0**: 스마트 병렬 처리, 대화형 러너, 스마트 스킵 등

자세한 내역: [00.CHANGELOG/CHANGELOG_v4.2.0.md](00.CHANGELOG/CHANGELOG_v4.2.0.md)

---

## 라이선스

MIT License

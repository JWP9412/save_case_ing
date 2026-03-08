# case-ing

대법원 나의 사건 조회 자동화 시스템 (Puppeteer + Python GUI) - v4.2.2

## 원본 출처

이 프로젝트는 [iicdii/case-ing](https://github.com/iicdii/case-ing)를 기반으로 하여 **Puppeteer 기반 병렬 처리** 및 **Python GUI 일괄 처리 시스템**으로 전환한 포크 버전입니다.

**원본 저장소**: https://github.com/iicdii/case-ing  
**포크 저장소**: https://github.com/JWP9412/save_case_ing

<a href="https://github.com/iicdii/case-ing/blob/master/LICENSE" alt="License">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg" />
</a>

case-ing는 case + ~ing의 합성어로 여러 개의 사건 진행현황을 쉽게 조회하도록 도와주는 자동화 도구입니다.

---

## 현재 버전 특징 (v4.2.2)

### 주요 개선 사항

1. **구조적 리팩터링 (batch_gui_maker.py 다이어트)** *(v4.2.2 신규)*
   - 메인 GUI 파일인 `batch_gui_maker.py`의 비대해진 코드를 서비스 모듈로 분리.
   - 사건 처리 핵심 로직을 `services/process_controller.py`로 이전하여 코드 가독성 및 유지보수성 향상.
   - 파일 I/O 및 히스토리 관리를 `services/history_manager.py`로 독립시켜 책임 소재 명확화.

2. **안정성 및 오류 처리 강화** *(v4.2.2)*
   - 병렬 처리 중 발생할 수 있는 UI 프리징 현상 개선 및 스레드 안정성 확보.
   - 사건 조회 실패 시 사용자 알림 및 실패 건 대상 자동 재실행 기능 도입.
   - `HistoryManager` 간 명칭 충돌 해결 및 로그 로딩 로직 안정화.

3. **UI/UX 일관성 확보** *(v4.2.2)*
   - 제어 패널 내 모든 버튼의 높이와 크기를 통일하여 정돈된 UI 제공.
   - 설정 버튼 및 이메일 발송 버튼의 활성화 상태에 따른 색상 구분 강화.
   - 과거 로그 뷰어에 클립보드 복사 버튼 추가.

4. **알림메일 고도화** *(v4.2.0)*
   - 메일 본문 HTML 표 생성 및 시트별 그룹화. GAS 웹 앱 연동을 통한 즉시 발송 지원.

5. **로깅 시스템 강화** *(v4.2.0)*
   - 실행마다 개별 로그 파일 생성 및 최대 10개 유지 관리 정책 도입.

---

## 프로젝트 구조

```
case-ing/
├── batch_gui_maker.py           메인 GUI (UI 구성 및 이벤트 위임)
├── config.py                    설정 상수 (APP_VERSION = "4.2.2" 등)
├── maintenance.js                유지보수 설정 (브라우저 표시 여부)
├── main.py                      진입점 (run_app 호출)
├── package.json                 Node.js 패키지 (Cypress 제거 및 정리)
├── requirements.txt             Python 패키지
├── logs/                        로그 파일 (최대 10개 유지)
│
├── src/                         Puppeteer 자동화 코드
│   ├── interactive_runner.js    대화형 Puppeteer 실행
│   └── PageController.js        페이지 자동화 로직
│
├── services/                    Python 서비스 모듈
│   ├── process_controller.py     사건 처리/병렬 실행 총괄 (v4.2.2)
│   ├── history_manager.py       검색 로그/상태 히스토리 관리 (v4.2.2)
│   ├── logger_service.py       전역 로거 및 파일 관리
│   ├── puppeteer.py             Node.js 프로세스 통신
│   ├── google_sheets.py        구글 시트 연동
│   └── update_history.py       증분 업데이트용 기록
│
├── gui/                         GUI 컴포넌트
│   ├── main_window.py          창 조립
│   ├── panels/                 헤더, 제어(2줄 버튼), 설정, 사건 목록, 진행상황
│   └── dialogs/                 설정, 과거 로그 뷰어, 캡차 입력
│
├── utils/                       공통 유틸 (email_manager 등)
├── gas/                         GAS 스크립트 (즉시 발송 지원)
├── api/certification/           구글 API 인증
├── assets/                      배너 등 에셋
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

---

## 개발 히스토리

- **v4.2.2**: batch_gui_maker.py 리팩터링, 프로세스 컨트롤러 분리, UI 일관성 강화
- **v4.2.0**: 알림메일 고도화(HTML·그룹화·즉시 발송), 제어 패널 UI·로깅 강화
- **v4.1.2**: 리팩토링(사건 목록 UI 분리), utils 폴더 추가
- **v4.1.0**: 표준 로깅, 로그 복사/과거 로그 뷰어, 사건 목록(N), 가로 스크롤바 수정
- **v4.0.0**: 배너 이미지 크기 최적화 및 PIL 전달

자세한 내역: [00.CHANGELOG/CHANGELOG_v4.2.2.md](00.CHANGELOG/CHANGELOG_v4.2.2.md)

---

## 라이선스

MIT License

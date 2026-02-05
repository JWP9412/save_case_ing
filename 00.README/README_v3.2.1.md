# case-ing

대법원 나의 사건 조회 자동화 시스템 (Puppeteer + Python GUI) - v3.2.1

## 원본 출처

이 프로젝트는 [iicdii/case-ing](https://github.com/iicdii/case-ing)를 기반으로 하여 **Puppeteer 기반 병렬 처리** 및 **Python GUI 일괄 처리 시스템**으로 전환한 포크 버전입니다.

**원본 저장소**: https://github.com/iicdii/case-ing  
**포크 저장소**: https://github.com/JWP9412/save_case_ing

<a href="https://github.com/iicdii/case-ing/blob/master/LICENSE" alt="License">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg" />
</a>

case-ing는 case + ~ing의 합성어로 여러개의 사건 진행현황을 쉽게 조회하도록 도와주는 자동화 도구입니다.

---

## 현재 버전 특징 (v3.2.1)

### 주요 개선 사항

1. **런타임 안정성 강화 (Runtime Stability)** *(v3.2.1 신규)*
   - `BatchProcessingGUI` 실행 시 발생하던 `RuntimeError: no default root window` 문제를 해결했습니다.
   - Tkinter 변수(`tk.BooleanVar`) 초기화 시점을 `create_window` 호출 이후로 최적화하여 GUI 시작 시의 불안정성을 제거했습니다.

2. **버전 및 설정 관리 일원화** *(v3.2.1 신규)*
   - 앱 버전(`APP_VERSION`), 창 제목(`APP_TITLE`), 부제목(`APP_SUBTITLE`) 정보를 `config.py` 한 곳에서만 관리하도록 개선했습니다.
   - 하드코딩된 버전 문자열을 제거하여 버전 업그레이드 시 유지보수 편의성을 높였습니다.

3. **스크래핑 로직 안정화 (Scraping Improvements)** *(v3.2.1 신규)*
   - **로딩 대기 강화**: 검색 결과 대기 로직을 강화하여 상세 페이지 진입 및 탭 인식 성공률을 높였습니다.
   - **그리드 탐색 예비 전략**: 기본 그리드 선택자 실패 시 탭 영역 내의 표를 자동으로 탐색하는 Fallback 로직을 추가하여 데이터 추출 안정성을 확보했습니다.

### 기존 주요 기능 (v3.2.0)
- **스마트 병렬 처리**: 사건 수에 비례하여 병렬 처리 수(1~20) 자동 계산 및 인스턴스 확장
- **대화형 러너**: 단일 지속 프로세스 모델로 캡차 이미지 유지 및 소켓 연결 안정성 확보
- **스마트 스킵**: 최근 검색 기록 활용 및 'CLICK' 입력 지원으로 처리 속도 향상

---

## 프로젝트 구조

```
case-ing/
├── batch_gui_maker.py           메인 GUI 프로그램
├── config.py                    설정 상수 (버전 및 타이틀 관리 추가)
├── main.py                      진입점
├── package.json                 Node.js 패키지
├── requirements.txt             Python 패키지
├── search_log.json              검색 성공 이력
│
├── src/                         Puppeteer 자동화 코드
│   ├── interactive_runner.js    대화형 Puppeteer 실행 (핵심 엔진)
│   ├── PageController.js        페이지 자동화 로직 (입력, 클릭, 추출 보완)
│   └── BrowserManager.js        브라우저 인스턴스 관리
│
├── services/                    Python 서비스 모듈
│   ├── puppeteer.py             Node.js 프로세스 통신 및 제어
│   ├── google_sheets.py         구글 시트 연동 로직
│   └── update_history.py       로컬 업데이트 기록
│
├── gui/                         GUI 컴포넌트
├── api/certification/           구글 API 인증
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
- `config.py`에서 `GOOGLE_SHEET_ID` 설정

### 3. 프로그램 실행
```bash
python batch_gui_maker.py
```

---

## 개발 히스토리

- **v3.2.1**: 런타임 오류 수정, 버전 관리 일원화, 스크래핑 안정성 강화
- **v3.2.0**: 스마트 병렬 처리, 쿠키·검색 기록 동기화, 상태 텍스트 세분화
- **v3.1.0**: 대화형 러너, 스마트 스킵, 이중 전략 데이터 추출
- **v3.0.0**: Puppeteer 기반 Python GUI 일괄 처리

자세한 내역: `00.CHANGELOG/CHANGELOG_v3.2.1.md`

---

## 라이선스

MIT License

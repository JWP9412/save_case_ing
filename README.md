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
   - 제어 패널 "모든 사건 메일 발송" 버튼으로 미발송 내역을 구글 시트 '알림메일'에 기록 후 GAS 발송.
   - 메일 본문 HTML 표에 구글 시트 색상 반영. 시트(피고·사건명)별 단락 구분.
   - 설정에서 수신 주소·GAS 웹 앱 URL 입력. 웹 앱 URL 설정 시 버튼 클릭 즉시 발송.

2. **제어 패널 UI 개선** *(v4.2.0)*
   - 버튼 2줄 배치·문구 간소화. 높이·모서리 통일. 설정 버튼 진한 색. 메일 버튼은 보낼 내역 있을 때만 활성(파란색).

3. **로깅 시스템 강화** *(v4.2.0)*
   - 실행마다 새 로그 파일(`logs/app_YYYYMMDD_HHMMSS.log`). 10개 초과 시 자동 삭제. 과거 로그 뷰어에 "클립보드에 복사" 버튼.

4. **리팩토링 및 구조 정리** *(v4.1.2)*
   - 사건 목록 UI를 `gui/panels/case_list_panel.py`로 분리. `utils/` 폴더 추가.

5. **표준 로깅 및 로그 뷰어** *(v4.1.0)*
   - `logs/app.log`에 날짜별 순환 저장. 진행상황 패널과 동기화되는 GUI 로그 핸들러.
   - 진행상황 하단 "복사" 버튼으로 로그 전체 클립보드 복사, "과거 로그" 버튼으로 이전 로그 파일 조회.

6. **사건 목록 UI 개선** *(v4.1.0)*
   - 제목에 현재 사건 개수 표시: "사건 목록(N)".
   - 사건 목록 가로 스크롤바 정상 작동 수정.

7. **배너 이미지 표시 및 크기 최적화** *(v4.0.0)*
   - 상단 배너 이미지가 CustomTkinter 요구사항(PIL Image 객체)에 맞게 정상 표시.
   - 배너 영역 높이(120px)에 맞춰 이미지 크기, 가로 최대 900px.

8. **사건 목록 열 너비 UX (Excel 스타일)** *(v3.3.0)*
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
├── config.py                    설정 상수 (APP_VERSION = "4.2.0" 등)
├── main.py                      진입점 (run_app 호출)
├── requirements.txt             Python 패키지
├── package.json                 Node.js 패키지
├── logs/                        로그 파일 (app_YYYYMMDD_HHMMSS.log, 최대 10개)
├── src/                         Puppeteer 자동화 코드
├── services/                    Python 서비스 (logger, puppeteer, google_sheets 등)
├── gui/                         GUI (main_window, panels, dialogs, captcha_dialog)
├── utils/                       공통 유틸 (email_manager 등)
├── gas/                         GAS 스크립트 (SendNotificationMail.gs)
├── api/certification/           구글 API 인증
├── assets/                      배너 등 에셋
└── 00.CHANGELOG, 00.README, 00.PROJECT_STRUCTURE   버전별 문서
```

---

## 빠른 시작

### 1. 사전 준비
- **Node.js** >= 14, **Python** >= 3.7
- 의존성: `npm install`, `pip install -r requirements.txt`

### 2. 구글 시트 설정
- 서비스 계정 설정 및 `api/certification/service-account.json` 저장
- `config.py` 또는 앱 내 설정 다이얼로그에서 `GOOGLE_SHEET_ID` 설정

### 3. 실행
```bash
python main.py
```

---

## 사용법

1. **사건 목록 불러오기**
   - 제어 패널에서 **「새로고침」** 버튼을 누르면 구글 시트의 사건 목록이 로드됩니다.
   - 사건 목록 시트 이름을 `config.py` 또는 앱 상단 설정(⚙)에서 일치하게 작성해야 합니다. 

2. **처리할 사건 선택**
   - 왼쪽 사건 목록에서 처리할 사건의 **체크박스**를 선택합니다.
   - 상단 「전체 선택」으로 한 번에 선택/해제할 수 있습니다.
   - 검색창에 키워드를 입력한 뒤 **「찾기」**로 목록을 필터링할 수 있습니다.

3. **옵션 설정 (선택)**
   - 설정 패널에서 **병렬 처리 수**, **캡차 재시도 횟수**, **재시도 대기 시간** 등을 조절할 수 있습니다.

4. **캡차 이미지 로드**
   - **「사건 조회 로드」** 버튼을 누르면 선택한 사건들의 캡차 이미지가 로드됩니다.
   - 각 행의 캡차 이미지와 입력란에 숫자를 입력합니다. (스마트 스킵 시 'CLICK' 입력 가능)

5. **처리 실행**
   - 모든 선택 사건에 캡차를 입력한 뒤 **「캡차 입력 완료」** 버튼을 누르면 실제 조회·크롤링이 시작됩니다.
   - 진행 상황은 오른쪽 **진행상황** 패널에서 확인할 수 있습니다.
   - 중간에 멈추려면 **「처리 중지」** 버튼을 누릅니다.

6. **결과 확인**
   - 처리된 진행내용은 구글 시트의 해당 사건 시트(피고_사건명_사건번호_법원)에 자동 저장됩니다.
   - 진행상황 로그는 **「복사」**로 클립보드에 복사하거나 **「과거 로그」**로 이전 로그 파일을 볼 수 있습니다.

---

## 개발 히스토리

- **v4.2.0**: 알림메일 고도화(HTML·그룹화·즉시 발송), 제어 패널 UI·로깅 강화
- **v4.1.2**: 리팩토링(사건 목록 UI 분리), utils 폴더 추가
- **v4.1.0**: 표준 로깅, 로그 복사/과거 로그 뷰어, 사건 목록(N), 가로 스크롤바 수정
- **v4.0.0**: 배너 이미지 PIL 전달 및 크기 최적화
- **v3.3.0**: 열 너비 Excel 스타일 UX, 열 너비 저장/복원
- **v3.2.x ~ v3.0.0**: 스마트 병렬 처리, 대화형 러너, 스마트 스킵 등

상세 변경 이력: [00.CHANGELOG/CHANGELOG_v4.2.0.md](00.CHANGELOG/CHANGELOG_v4.2.0.md)  
버전별 README: [00.README/](00.README/)

---

## 라이선스

MIT License

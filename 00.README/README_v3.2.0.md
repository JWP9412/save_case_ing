# case-ing

대법원 나의 사건 조회 자동화 시스템 (Puppeteer + Python GUI)

## 원본 출처

이 프로젝트는 [iicdii/case-ing](https://github.com/iicdii/case-ing)를 기반으로 하여 **Puppeteer 기반 병렬 처리** 및 **Python GUI 일괄 처리 시스템**으로 전환한 포크 버전입니다.

**원본 저장소**: https://github.com/iicdii/case-ing  
**포크 저장소**: https://github.com/JWP9412/save_case_ing

<a href="https://github.com/iicdii/case-ing/blob/master/LICENSE" alt="License">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg" />
</a>

case-ing는 case + ~ing의 합성어로 여러개의 사건 진행현황을 쉽게 조회하도록 도와주는 자동화 도구입니다.

---

## 현재 버전 특징 (v3.2.0)

### 주요 기능

1. **스마트 병렬 처리 (Smart Parallel Processing)** *(v3.2.0 신규)*
   - 사건 목록 로드 시 **병렬 처리 수**를 **사건 수의 절반**으로 자동 계산하여 설정합니다.
   - 예: 사건 30개 → 인스턴스 15개 자동 생성 및 병렬 가동. `cookie_data_for_save/instance_N` 폴더가 사건 수에 맞춰 유기적으로 확장됩니다.
   - 최대 20개까지 설정 가능하며, 10개 초과 시 디스크/RAM 사용량 경고 로그가 출력됩니다.
   - 쿠키 폴더(`cookie_data_for_save`)를 삭제한 경우, 검색 기록(`search_log.json`)도 자동으로 초기화되어 '기록' 열 표시와 실제 데이터가 일치합니다.

2. **대화형 러너 (Interactive Runner) & 단일 지속 프로세스**
   - 브라우저를 껐다 켜거나 재연결하는 방식 대신, **하나의 프로세스가 계속 실행**되는 구조로 변경하여 안정성을 극대화했습니다.
   - **캡차 이미지 유지**: 브라우저 세션이 끊기지 않으므로, 캡차 캡처 후 입력 단계까지 이미지가 절대 바뀌지 않습니다.
   - **소켓 연결 오류 해결**: 메모리 관리 옵션 최적화로 브라우저 비정상 종료를 방지합니다.

3. **스마트 스킵 (Smart Skip)**
   - **'CLICK' 입력 지원**: 캡차 입력란에 'CLICK'을 입력(또는 자동 입력)하면 캡차 입력을 건너뛰고 최근 검색 기록을 클릭하여 빠르게 조회합니다.
   - **쿠키 지속성**: 브라우저 세션과 쿠키를 유지하여 재검색 시 불필요한 입력을 최소화합니다.

4. **향상된 데이터 추출 및 자동화**
   - **강력한 탭/그리드 탐색**: ID 변경에 대응하는 텍스트 기반 검색과 이중 전략(Dual Strategy)으로 '진행내용' 탭을 확실하게 찾아냅니다.
   - **입력 오류 방지**: 사건번호와 당사자명 입력 시 재클릭 및 포커스 로직을 추가하여 WebSquare 프레임워크의 인식 오류를 해결했습니다.
   - **페이지 새로고침 방지**: 검색 버튼 클릭 로직을 개선하여 불필요한 페이지 리로드를 막았습니다.

5. **Python GUI 일괄 처리 시스템**
   - 구글 시트에서 사건 목록 자동 로드
   - 여러 사건을 동시에 처리 (병렬 처리, v3.2.0에서 1~20개 자동 권장)
   - 캡차 이미지 자동 캡처 및 수동 입력
   - 진행내용 자동 추출 및 구글 시트 저장

6. **구글 시트 연동**
   - 사건 목록 자동 읽기
   - 진행내용 자동 저장
   - 워크시트 자동 생성 (피고_비고_사건번호_법원)
   - 업데이트 일시 및 이전 업데이트 기록

---

## 프로젝트 구조

```
case-ing/
├── batch_gui_maker.py           메인 GUI 프로그램
├── config.py                    설정 상수 (MAX_PARALLEL_LIMIT=20)
├── main.py                      진입점
├── package.json                 Node.js 패키지
├── requirements.txt             Python 패키지
├── search_log.json              검색 성공 이력 (기록 열 표시용)
│
├── src/                         Puppeteer 자동화 코드
│   ├── interactive_runner.js    대화형 Puppeteer 실행 (핵심 엔진)
│   ├── PageController.js        페이지 자동화 로직 (입력, 클릭, 추출)
│   ├── index.js                 (구버전 호환용)
│   ├── single-case-captcha.js   (구버전 호환용)
│   └── BrowserManager.js        브라우저 인스턴스 관리
│
├── services/                    Python 서비스 모듈
│   ├── puppeteer.py             Node.js 프로세스 통신 및 제어
│   ├── google_sheets.py         구글 시트 연동 로직
│   └── update_history.py       로컬 업데이트 기록
│
├── gui/                         GUI 컴포넌트 (캡차 다이얼로그 등)
├── api/certification/           구글 API 인증
├── screenshots/                 캡차 이미지 저장소
├── results/                     처리 결과 JSON 저장소
├── cookie_data_for_save/        브라우저 세션 (instance_0 ~ instance_N)
└── 00.CHANGELOG, 00.README, 00.PROJECT_STRUCTURE   버전별 문서
```

---

## 빠른 시작

### 1. 사전 준비

#### 필수 소프트웨어
- **Node.js** >= 14
- **Python** >= 3.7
- **npm** (Node.js와 함께 설치됨)

#### 의존성 설치

```bash
npm install
pip install -r requirements.txt
```

### 2. 구글 시트 설정

- 구글 스프레드시트 생성 (사건 목록 시트: 사건번호, 피고, 법원, 비고)
- 서비스 계정 설정 및 `api/certification/service-account.json` 저장
- 스프레드시트에 서비스 계정 이메일 편집자 권한 추가
- `config.py`에서 `GOOGLE_SHEET_ID` 확인

자세한 설정: [`api/certification/GOOGLE_AUTH_SETUP.md`](api/certification/GOOGLE_AUTH_SETUP.md)

### 3. 프로그램 실행

```bash
python batch_gui_maker.py
```

---

## 사용 방법

### 1. 구글 시트 로드
- **"새로고침"** 버튼 클릭 → 사건 목록 자동 로드. v3.2.0에서는 **병렬 처리 수**가 사건 수에 맞춰 자동 설정됩니다.

### 2. 처리할 사건 선택
- 체크박스로 처리할 사건 선택.

### 3. 처리 설정
- **병렬 처리 수**: 1~20 (로드 시 사건 수의 절반으로 자동 권장. 수동 변경 가능)
- **캡차 재시도 횟수**, **재시도 간 대기시간**: 필요 시 조정

### 4. 캡차 이미지 로드
- **"캡차 이미지 로드"** 클릭 → 선택한 사건의 캡차 이미지 캡처.

### 5. 캡차 입력
- 6자리 숫자 입력 후 Enter → 다음 입력칸 이동. 모두 입력 후 **"캡차 입력 완료"** 클릭.

### 6. 자동 처리
- 검색 실행 → 진행내용 추출 → 구글 시트 저장 → 상태 업데이트.

---

## GUI 기능 설명

### 제어 패널
- **새로고침**: 구글 시트에서 사건 목록 가져오기 (병렬 수 자동 계산)
- **전체 선택 / 전체 해제**
- **캡차 이미지 로드**: 선택 사건 캡차 캡처
- **캡차 입력 완료**: 캡차 입력 후 처리 시작
- **처리 중지**: 진행 중인 처리 중지

### 처리 설정
- **병렬 처리 수** (1~20): 로드 시 사건 수의 절반으로 자동 권장. 인스턴스 폴더(`cookie_data_for_save/instance_N`) 개수와 동일.
- **캡차 재시도 횟수**, **재시도 간 대기시간**

### 사건 목록
- **선택**, **사건번호**, **피고**, **법원**, **비고**, **캡차 이미지**, **캡차 입력**
- **상태**: 대기, 입력대기, **처리중(캡차로딩)**, **처리중(크롤링)**, **처리중(시도)**, **처리중(저장)**, 완료, 실패 등
- **기록**: 검색함 / - (쿠키·검색 기록 동기화)
- **최근 업데이트**: 마지막 업데이트 일시 및 D+n

### 진행상황 패널
- 실시간 로그 (처리 진행, 구글 시트 저장, 용량 경고 등)

---

## 기술 스택

- **Backend**: Puppeteer, Node.js (interactive_runner.js, PageController.js)
- **Frontend**: Python Tkinter, gspread, Pillow, Threading
- **데이터**: Google Sheets API, JSON (search_log, update_history)

---

## 처리 흐름

1. 구글 시트 로드 (병렬 수 자동 계산)
2. 사건 선택
3. 캡차 이미지 캡처 (Puppeteer, instance_N)
4. 사용자 캡차 입력
5. 자동 검색 실행 → 진행내용 추출
6. 구글 시트 저장
7. 완료

---

## 문제 해결

- **GUI/패키지 오류**: `python --version`, `pip install -r requirements.txt --upgrade`
- **구글 시트 연결**: `service-account.json` 존재, 스프레드시트 권한, API 활성화 확인
- **캡차 미표시**: `screenshots/` 확인, `npm install`
- **브라우저 미종료**: "처리 중지" 클릭 또는 Chrome 프로세스 수동 종료

---

## 개발 히스토리

- **v3.2.0**: 스마트 병렬 처리, 쿠키·검색 기록 동기화, 상태 텍스트 세분화, Config Limit 20
- **v3.1.0**: 대화형 러너, 스마트 스킵, 이중 전략 데이터 추출
- **v3.0.0**: Puppeteer 기반 Python GUI 일괄 처리

자세한 내역: `00.CHANGELOG/CHANGELOG_v3.2.0.md`

---

## 라이선스

MIT License

---

## 감사의 말

이 프로젝트는 [iicdii/case-ing](https://github.com/iicdii/case-ing)를 기반으로 합니다.

---

## 문의

**GitHub Issues**: https://github.com/JWP9412/save_case_ing/issues

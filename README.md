# case-ing (미어캣싱)

대법원 나의 사건 조회 자동화 시스템 (Puppeteer + Python GUI) - **v5.1.2**  
제품 UI 명칭: **미어캣싱** (저장소/폴더명 case-ing 유지)

- 개발자 : 박지원 -

공식 버전 순서: **v5.1.1 → v5.1.2**

## 원본 출처

이 프로젝트는 [iicdii/case-ing](https://github.com/iicdii/case-ing)를 기반으로 하여 **Puppeteer 기반 병렬 처리** 및 **Python GUI 일괄 처리 시스템**으로 전환한 포크 버전입니다.

**원본 저장소**: https://github.com/iicdii/case-ing  
**포크 저장소**: https://github.com/JWP9412/save_case_ing

<a href="https://github.com/iicdii/case-ing/blob/master/LICENSE" alt="License">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg" />
</a>

case-ing는 case + ~ing의 합성어로 여러 개의 사건 진행현황을 쉽게 조회하도록 도와주는 자동화 도구입니다.

---

## 프로젝트 구조

```
case-ing/
├── auto_runner.py               CLI 실행기
├── config.py                    설정 상수 (APP_VERSION = "5.1.2", APP_TITLE = "미어캣싱")
├── main.py                      진입점 (GUI 또는 --auto)
├── requirements.txt             Python 패키지
├── data/                        설정·이력 JSON
├── ocr_export/                  캡차 OCR
├── src/                         Puppeteer(Node) 자동화
├── services/                    비즈니스 로직 (process_controller 패키지 등)
├── 99.Error case/               사고 기록 (재발 방지)
├── gui/                         UI (설정·달력·진행상황 등)
├── assets/app_icon.ico          앱 아이콘
├── 실행.bat                     GUI 더블클릭 실행
├── scripts/build_portable.ps1   Windows 포터블 빌드
├── gas/                         GAS 스크립트 (즉시 발송)
└── 00.CHANGELOG, 00.README      버전별 문서
```

---

## 사용법

### 1. 준비물

| 항목 | 설명 |
|------|------|
| OS | Windows 권장 (개발·테스트 기준) |
| Python | 3.10 이상 |
| Node.js | Puppeteer(`src/`) 실행용 (LTS 권장) |
| Chrome | 일반 설치 Chrome, 또는 포터블 빌드에 동봉된 런타임 |
| 구글 OAuth | Google Cloud에서 발급한 `client_secret.json` (데스크톱 앱) |
| 구글 시트 | 사건 목록이 있는 스프레드시트 (편집 권한 있는 계정) |

포터블(`CaseIng.exe`)만 쓸 경우 Python·Node 별도 설치는 생략할 수 있습니다. → [7. Windows 포터블](#7-windows-포터블)

### 2. 설치

```bash
# 저장소 받기
git clone https://github.com/JWP9412/save_case_ing.git
cd save_case_ing

# Python 패키지
pip install -r requirements.txt

# Puppeteer(Node) 의존성
cd src
npm install
cd ..
```

OCR(Tesseract)을 쓰려면 PC에 [Tesseract-OCR](https://github.com/tesseract-ocr/tesseract)이 설치되어 있어야 할 수 있습니다. EasyOCR이 되면 Tesseract는 폴백으로 쓰입니다.

### 3. 최초 설정 (설정 창)

1. 앱 실행
   - 더블클릭: `실행.bat`
   - 또는 터미널: `python main.py`
   - 창 제목: **미어캣싱**
2. 상단/제어 영역의 **「설정」** 버튼을 누릅니다.
3. **구글 시트** 탭
   - 스프레드시트 ID, OAuth `client_secret.json` 경로 등을 입력
   - **「Google 연동」**으로 브라우저 로그인·토큰 저장
4. **사건 조회 설정** 탭
   - 병렬 처리 수, 캡차 재시도 횟수, 재시도 대기(초)
   - **적용**(저장 후 창 유지) 또는 **확인**(적용 후 닫기)
5. **테마** 탭
   - 다크 / 라이트 / 시스템 → 적용·확인
6. 첫 실행 가이드 창이 뜨면 안내에 따릅니다. (나중에 설정에서 다시 열 수 있음)

### 4. 일상 조회 흐름 (클릭 순서)

1. **새로고침 (F5)**  
   구글 시트에서 사건 목록을 불러옵니다. (캐시가 있으면 시작 시 먼저 보이고, F5로 최신화)
2. 조회할 사건의 **체크박스**를 선택합니다.
3. **「▶ 사건 기록 수집 실행」**을 누릅니다.  
   브라우저(프로필)가 뜨고 캡차 화면까지 진행됩니다.
4. **캡차**
   - **OCR 성공**: 입력칸에 숫자가 채워지고, 설정상 자동 제출이면 **「캡차 입력 완료」를 누르지 않아도** 다음 단계로 진행됩니다.
   - **OCR 실패·수동**: 숫자를 직접 입력한 뒤 **「캡차 입력 완료」**를 누릅니다.
5. 우측 **「진행상황」**에서 로그를 확인합니다.
   - 마우스 휠·스크롤바, 드래그로 줄 선택, Ctrl+C / 「복사」
   - 「숨기기」로 패널을 접을 수 있습니다.
6. 완료되면 구글 시트(개별 사건 탭)와 로컬 `data/` 이력에 반영됩니다.

중지하려면 **「■ 처리 중지」**를 누릅니다.

### 5. 자주 쓰는 화면 기능

| 기능 | 어디서 | 하는 일 |
|------|--------|---------|
| **달력** | 사건 목록 행, 「사건목록 관리」 왼쪽 | 변론·감정·판결 기일 월간 보기 |
| **사건목록 관리** | 같은 행 오른쪽 | 사건 추가·수정·숨기기 등 |
| **특정 기간 조회** | 제어 패널 | 기간만 모아 미리보기·메일 (시트에 안 씀) |
| **사건 시트 관리 ▾** | 제어 패널 | 중복 오류 제거 / 기록 초기화·재수집 / 시트-대법원 대조 |
| **보기** | 피고/사건명 칸 | 일반내용(기본내용·기일·서류·당사자·대리인) |
| **버전 업데이트 확인** | 제어 패널 | GitHub 최신 릴리스·태그와 로컬 버전 비교 |
| **알림 메일** | 제어 패널 | 조회 결과 요약 메일 (설정에 수신 주소·GAS URL) |

### 6. CLI 자동 실행

작업 스케줄러 등으로 백그라운드 주기 조회할 때:

```bash
python main.py --auto
```

GUI와 같은 조회 파이프라인을 쓰며, 결과는 메일/이력에 누적될 수 있습니다.

### 7. Windows 포터블

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build_portable.ps1
```

결과 폴더 `case-ing-portable\`의 `CaseIng.exe`를 실행합니다.  
상세: [`docs/DEPLOY_WINDOWS.md`](docs/DEPLOY_WINDOWS.md)

### 8. 짧은 FAQ

| 증상 | 확인 |
|------|------|
| Google 미연동 / 시트 로드 실패 | 설정 → 구글 시트 → ID·`client_secret`·「Google 연동」, 시트 공유 권한 |
| 목록이 비어 있음 | F5 새로고침, 스프레드시트 ID·워크시트 이름 |
| 캡차가 안 넘어감 | OCR 실패 시 수동 입력 후 「캡차 입력 완료」 |
| Chrome Code 21 / 프로필 충돌 | 설정에서 **병렬 처리 수**를 낮추고 재시도 |
| node 검은 창이 많이 뜸 | v4.12.1부터 Windows에서는 숨김. 구버전이면 업데이트 |
| 새 버전 있는지 | 「버전 업데이트 확인」버튼 |

---

## 현재 버전 특징 (v5.1.2)

1. **실패 집계 수정** — 여러 파도로 나뉜 배치에서도 실패 건수가 맞게 집계됩니다.
2. **진행내용 탭/그리드 안정화** — 탭 전환을 검증하고, Node 종료 시 브라우저를 재기동해 재시도합니다.
3. **OCR 신뢰도** — Tesseract 가짜 1.00 제거, 오독 자동 제출 감소.
4. **Chrome 재사용** — 프로필(레인)당 브라우저 1개 상주. 설정에서 프로필 수 조절.
5. **속도·메모리** — EasyOCR 워밍업, 리소스 차단, 캐시/스크린샷 정리, OCR 유휴 언로드.
6. **캡차 학습 데이터** — 성공/실패 캡차를 `data/captcha_dataset/`에 자동 수집.

---

## 개발 히스토리

- **v5.1.2**: 실패 집계·탭/그리드·OCR conf·Chrome 재사용·메모리/속도·캡차 데이터셋
- **v5.1.1**: 시작 버튼 TypeError 수정, 진행상황 스크롤바·전체 복사 버그 수정
- **v5.1.0**: 시트 보호·메일 결과변경 분리·캡차/OCR 안정화·ProcessController 패키지 분리
- **v5.0.0**: 4.12.1 이후 누적 기능 통합 릴리스 (기일 달력·설정·OCR·진행상황·기간조회·시트 관리 등)
- **v4.12.1**: Windows node.exe 콘솔 창 숨김 (CREATE_NO_WINDOW)
- **v4.12.0**: 일반내용 돋보기 뷰어
- **v4.11.0**: 앱 아이콘(미어캣+저울), 실행.bat
- **v4.10.0**: 기간 조회·시트 대조, 메일 요약 누적
- **v4.9.0**: 캡차 OCR, Windows 포터블
- **v4.8.0**: 구글 시트 429 완화
- **v4.7.0**: 구글 캘린더·OAuth, 기록 초기화·재수집
- **v4.6.x ~ v4.0.0**: 목록 캐시·관리 UI, 아키텍처, CLI, 알림메일 등

상세 변경 이력: [00.CHANGELOG/CHANGELOG_v5.1.2.md](00.CHANGELOG/CHANGELOG_v5.1.2.md)  
버전별 README: [00.README/README_v5.1.2.md](00.README/README_v5.1.2.md)  
구조: [00.PROJECT_STRUCTURE/PROJECT_STRUCTURE_v5.1.2.md](00.PROJECT_STRUCTURE/PROJECT_STRUCTURE_v5.1.2.md)

---

## 라이선스

MIT License

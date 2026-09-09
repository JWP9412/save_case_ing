# CHANGELOG v5.3.0

## v5.3.0 주요 변경 (2026-09-09)

공식 버전 흐름: **v5.2.0 → v5.3.0**

### Bug Fixes

- **잔여 WORKER_IDLE 가짜 실패**
  - 이전 사건이 남긴 `WORKER_IDLE`을 다음 사건 캡차 대기가 읽어 “캡차 없이 IDLE”로 오판하던 문제 수정.
  - CASE 전송 전 stdout drain, 사건 시작 이전 IDLE 무시, 생존 워커는 레인 kill하지 않음.
  - Chrome 재기동 폭주·웨이브 연쇄 실패 완화.

- **스마트 스킵 상시 실패**
  - 검색 폼이 뜨기 전·`a`/`td` 정확 일치만·`about:blank`로 페이지를 비워 최근 검색을 못 찾던 문제 수정.
  - 검색 폼 대기 + 수 초 폴링 스캔 + 공백/하이픈 정규화 + 같은 레인에서 blank 제거.
  - 이미 조회·저장한 사건은 캡차 없이 CLICK 경로로 진행.

- **종국 오탐 (박종국 / 「종국결과」라벨)**
  - 진행내용 본문 `"종국" in text`·헤더 라벨을 종국으로 보던 로직 제거.
  - 기본내용 `basic['종국결과']` 실값만 판별 (`services/finalized_case.py`).

- **CLI 「수신 메일 주소 없음」**
  - `auto_runner.py`에 `config.load_user_settings()` 추가 (GUI `main.py`와 동일).
  - 설정 창에 저장한 `NOTIFICATION_EMAIL_ADDRESS`가 CLI에서도 적용됨.

- **조회 시작 시 taskkill CMD 창 번쩍임**
  - Windows `taskkill`에 `CREATE_NO_WINDOW` 적용 (`puppeteer.py`, `cleanup.py`). Chrome headless와 무관.

### Features & Improvements

- **종국 감지·숨김 후보**
  - 조회 성공 후 기본내용 종국결과 칸 기준으로 후보 수집. CLI는 대화상자 없이 감지만.

- **에이전트/개발 규칙**
  - `AGENTS.md`에 진입점·설정 로드 보호 조항 추가.
  - `99.Error case/`에 2026-09-09 사고 4건 문서화.

### Technical

- `config.py`: `APP_VERSION = "5.3.0"`.
- `services/puppeteer.py`: `_hidden_run`, `_drain_worker_stdout`, IDLE 잔여분 처리.
- `src/PageController.js`: `waitForSearchForm`, `scanRecentCase`.
- `src/interactive_runner.js`: 스마트 스킵 대기/스캔, about:blank 제거.
- `services/finalized_case.py`: 종국 판별·숨김 후보.
- `auto_runner.py`: `load_user_settings()`.
- `99.Error case/ERROR_20260909_*.md`, `AGENTS.md`.

### 이전 버전 요약 (v5.2.0)

- 실패 집계·탭/그리드·OCR conf·Chrome 재사용·메모리/속도·캡차 데이터셋.

# CHANGELOG v5.3.1

## v5.3.1 주요 변경 (2026-09-10)

공식 버전 흐름: **v5.3.0 → v5.3.1**

### Bug Fixes

- **CLI 브라우저 준비 타임아웃(줄 훔침)**
  - `_readline_with_timeout`이 타임아웃마다 새 스레드로 `stdout.readline()`을 호출해 `WORKER_READY`를 가로채던 문제 수정.
  - 레인당 읽기 스레드 1개 + `queue.Queue`로 교체. 준비 신호가 사라지지 않음.
  - `WORKER_READY`뿐 아니라 `CASE/QUIT 대기` 로그도 준비 완료로 판정.

- **CLI 숨긴 사건도 조회·메일에 포함**
  - `auto_runner.py`가 `hidden_cases.json`을 무시하고 시트 전체를 조회하던 문제 수정.
  - GUI와 동일하게 숨긴 사건을 제외한 뒤 조회·캡차·알림 메일 집계.

### Features & Improvements

- **Node READY 선행**
  - `interactive_runner.js`에서 `WORKER_READY`를 먼저 보내고, `puppeteer`/`PageController`는 그다음에 로드.
  - Python이 수십 초 동안 READY를 못 보던 콜드 스타트 대기 완화.

- **CLI 시작 시 고아 Node 청소**
  - GUI와 같이 배치 시작 직전에도 `kill_orphan_interactive_runners` 호출.
  - 이전 실행이 프로필을 잠가 첫 기동이 길어지는 경우 완화.

- **로그 문구 쉬운 말**
  - 「워커 READY」→「브라우저가 켜질 때까지 기다리는 중」/「브라우저 준비 완료」등.

### Technical

- `config.py`: `APP_VERSION = "5.3.1"`.
- `services/puppeteer.py`: 레인 stdout 큐·읽기 스레드, `_is_worker_ready_line`.
- `src/interactive_runner.js`: READY 후 `loadBrowserDeps()`.
- `auto_runner.py`: 숨김 필터, 시작 전 고아 청소.

### 이전 버전 요약 (v5.3.0)

- WORKER_IDLE 가짜 실패·스마트 스킵·종국결과 칸 판별·CLI 설정 로드·taskkill 숨김.

# CHANGELOG v5.1.0

## v5.1.0 주요 변경 (2026-09-02)

공식 버전 흐름: **v5.0.0 → v5.1.0**

### Features & Improvements

- **알림메일: 송달 결과 변경 분리**
  - 법원이 며칠 뒤 채우는 송달「결과」칸만 바뀐 행을「새 진행내용」과 구분.
  - 메일에 **「결과 변경 내역」** 표 추가 (`일자 | 내용 | 이전 결과 | 변경 결과`).
  - 요약 표에 **「성공(결과 변경)」** 칸 추가, 사건 상태 `완료 (결과변경 M건)`.

- **구글시트 진행내용 소실 방지 (3중 가드)**
  - Node: 그리드 추출 실패 시 빈 배열 대신 예외 전파.
  - Python: 대법원 0건 + 시트에 기존 행 있으면 덮어쓰기 중단.
  - `overwrite_progress_area`: 빈 데이터 덮어쓰기 기본 거부 (`allow_empty=False`).
  - 사고 기록: `99.Error case/ERROR_20260812_sheet_progress_wipe.md`.

- **캡차·OCR 안정화**
  - 수동 캡차 모아보기 창: 화면 밖 표시 수정, 항상 위·포커스.
  - 중지 후 OCR 자동 제출이 계속 돌던 문제 수정 (`_captcha_batch_running` 등).
  - 스마트 스킵 실패 시 캡차/OCR 정규 경로로 자동 폴백.
  - 스마트 스킵 상세 화면 렌더 대기 강화 (진행내용 그리드 미탐지 완화).

- **진행상황 로그**
  - 스크롤바 트랙·썸 대비 개선 (내용이 적어도 보이게).

### Refactoring

- **`services/process_controller/` 패키지 분리**
  - 기존 2,300줄 단일 파일 → mixin 패키지 (`hearing`, `captcha_ocr`, `result_handler`, `case_runner`, `cleanup`, `controller`).
  - 외부 import `from services.process_controller import ProcessController` 호환 유지.

### 이전 버전 요약 (v5.0.0)

- 기일 달력·지연 등록 비고·미어캣싱 제품명·설정 창 개편·진행상황 Canvas·OCR 자동 제출·기간조회·시트 관리 등.

## Technical

- `config.py`: `APP_VERSION = "5.1.0"`.
- `services/email_manager.py`: `result_changes`, `STATUS_RESULT_CHANGED`, `add_result_changes`.
- `services/process_controller/`: mixin 패키지 (기존 `process_controller.py` 삭제).
- `services/google_sheets.py`: `allow_empty` 가드, `_sheet_row_dc_key`.
- `services/puppeteer.py`, `src/PageController.js`, `src/interactive_runner.js`: 추출 실패·스마트 스킵.
- `gui/dialogs/manual_captcha_dialog.py`: 수동 캡차 모아보기.
- `99.Error case/`: 사고 기록 보관소.

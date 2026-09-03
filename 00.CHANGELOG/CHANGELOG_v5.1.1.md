# CHANGELOG v5.1.1

## v5.1.1 주요 변경 (2026-09-03)

공식 버전 흐름: **v5.1.0 → v5.1.1**

### Bug Fixes

- **「사건 기록 수집 실행」버튼 오류 수정**
  - v5.1.0 패키지 분리 시 `CaseRunnerMixin.start_processing`에 잘못 붙은 `@staticmethod` 제거.
  - 증상: `TypeError: start_processing() missing 1 required positional argument: 'cases'`.
  - `HearingMixin._normalize_text`의 `@staticmethod`도 원위치 복구.

- **진행상황 로그 스크롤바**
  - 스크롤바를 먼저 pack하고 캔버스 `width=1`로 좁은 패널에서도 오른쪽에 보이게 수정.
  - `tk.Scrollbar` → `ctk.CTkScrollbar` (Windows에서 대비 개선).

- **진행상황 「전체 복사」**
  - 복사 버튼이 선택한 한 줄만 복사하던 문제 수정 → 항상 전체 로그 복사.
  - 단순 클릭만 하면 선택 해제 (Ctrl+C는 선택 있으면 선택만).

### Technical

- `config.py`: `APP_VERSION = "5.1.1"`.
- `services/process_controller/case_runner.py`, `hearing.py`: `@staticmethod` 정리.
- `gui/panels/progress_panel.py`: 스크롤바·복사·클릭 선택 동작.
- `scripts/split_process_controller.py`: 데코레이터 줄 포함하도록 `parse_methods` 수정 (재분리 시 재발 방지).

### 이전 버전 요약 (v5.1.0)

- 알림메일 결과 변경 분리, 시트 3중 가드, 캡차/OCR 안정화, ProcessController 패키지 분리.

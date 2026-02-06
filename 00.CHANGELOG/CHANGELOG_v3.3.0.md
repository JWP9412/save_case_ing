# CHANGELOG v3.3.0 (2026-01-28)

## Features & Improvements

- **사건 목록 열 너비 UX (Excel 스타일)**
  - 드래그 중 가이드라인(세로선)만 표시하여 렉 없이 리사이즈.
  - 드롭 시 전체 UI 리빌드 없이 기존 위젯의 `width`만 갱신(`apply_column_width`).
  - 헤더·행 셀 참조(`header_cell_frames`, `case_cell_frames`)로 즉시 반영.

- **열 너비 저장/복원**
  - 사용자가 조절한 열 너비를 `column_widths.json`에 저장.
  - `load_column_widths()` / `_save_column_widths()` 추가, `config.COLUMN_WIDTHS_FILE` 설정.
  - UI 갱신 시 저장된 값 우선 적용, 리사이즈 종료 시 자동 저장.

- **캡차 입력란 오타 수정**
  - key 검증 시 삽입 문자가 빈 문자열(Backspace/Delete)인 경우 허용하여, 입력란에서 글자 삭제 가능.

- **브라우저 표시 설정 분리 (유지보수)**
  - 프로젝트 루트에 `maintenance.js` 추가: `browserHeadless: true` (기본 숨김).
  - `src/interactive_runner.js`, `src/single-case-captcha.js`에서 `maintenance.browserHeadless` 사용.
  - 디버깅 시 `maintenance.js` 한 곳만 수정하면 브라우저 창 표시 가능.

## Configuration

- **config.py**: `COLUMN_WIDTHS_FILE = 'column_widths.json'` 추가.

# CHANGELOG v4.10.0

## v4.10.0 주요 변경 (2026-08-06)

### Features & Improvements

- **UI 이모지 깨짐 정리**
  - 맑은 고딕에서 깨지던 이모지를 안전 문자(`▶` `■` 등) 또는 텍스트만으로 통일.
  - `gui/utils/glyphs.py` + `config.UI_USE_EMOJI` (기본 False).
  - 시작 버튼 문구: `▶ 사건 기록 수집 실행`.

- **메일 「이번 조회 결과 요약」 전체 사건 누적**
  - 배치마다 덮어쓰지 않고 `unsent_emails.json`의 `run_results`에 사건번호 단위로 병합.
  - 사건 목록 전체를 기준으로 성공/변경없음/실패/캡차/미조회 표기.
  - CLI `--auto` 결과도 같은 파일에 기록되어 GUI 메일에 합류.
  - 자동 실행이 이력 파일을 갱신하면 GUI에 새로고침(F5) 안내.

- **특정 기간 조회**
  - 제어 패널 `특정 기간 조회` 버튼.
  - 기본값 어제~오늘, 달력·프리셋(최근 7일/이번 달), 자유 형식 날짜 파서.
  - 대법원 재크롤링 후 기간 행만 모아 HTML/MD 미리보기·메일 발송.
  - 시트·update_history·unsent_emails에는 쓰지 않음(기존 조회와 겹치지 않음).
  - 메일 전 시트 존재 여부(있음/유사/없음) 대조 열 포함.

- **시트-대법원 대조**
  - 제어 패널 `시트-대법원 대조` 버튼.
  - 4열 키로 내용 단위 비교(일치/시트에만/대법원에만/결과만 다름).
  - 읽기 전용(시트 미기록), 결과는 미리보기·메일로 확인.

### 이전 버전 요약 (v4.9.0)

- 캡차 OCR 자동인식·자동제출, Windows 포터블 배포, 인증/시트 안내 보강.

## Technical

- `config.py`: `APP_VERSION = "4.10.0"`, `UI_USE_EMOJI`, `BTN_TEXT_*`.
- `gui/utils/glyphs.py`, `gui/panels/control_panel.py` (3행 버튼).
- `services/email_manager.py`: `record_run_results`, `run_results`, `all_cases` 요약.
- `services/date_utils.py`, `gui/dialogs/date_picker.py`, `period_query_dialog.py`.
- `services/sheet_compare.py`, `services/period_report.py`.
- `gui/dialogs/report_preview_dialog.py`.
- `gui/utils/batch_actions.py`: 기간 조회·시트 대조 플래그.
- `services/process_controller.py`: `is_period_mode` / `is_compare_mode` 분기.
- `auto_runner.py`: 변경없음 분리, `record_run_results` 공유.

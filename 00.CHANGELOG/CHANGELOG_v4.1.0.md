# CHANGELOG v4.1.0 (2026-01-28)

## Features & Improvements

- **표준 로깅 시스템 도입**
  - `services/logger_service.py` 신규: Python `logging` 기반 전역 로거.
  - 파일 핸들러: `logs/app.log`에 날짜별 순환 저장 (`TimedRotatingFileHandler`, 7일 보관).
  - GUI 핸들러: 진행상황 패널 `status_text` 위젯과 연동하는 `GuiLogHandler` (스레드 세이프).
  - `puppeteer.py`, `google_sheets.py`의 `print`/`log_callback` 제거 후 `logger.info` 등 표준 로거로 통일.

- **진행상황 패널 로그 기능**
  - 로그 창 하단에 "복사" 버튼: 현재 진행상황 로그 전체를 클립보드에 복사.
  - "과거 로그" 버튼: `gui/dialogs/log_viewer_dialog.py` 다이얼로그로 `logs/` 내 `app.log` 및 날짜별 순환 파일 선택·조회.
  - 과거 로그 뷰어: 파일 선택(OptionMenu), 새로고침, 폴더 열기, 대용량 시 마지막 N줄만 표시.

- **사건 목록 UI**
  - 제목을 "사건 목록"에서 "사건 목록(N)" 형태로 변경. 목록 갱신 시 개수 자동 반영.
  - 가로 스크롤바 작동 수정: scrollbar command를 `xview_moveto(first, last)` 대신 `xview(*args)`로 전달해 헤더/행 캔버스 동기 스크롤 정상화.

## Technical

- **batch_gui_maker.py**: `setup_logger()`, `register_gui_handler()` 호출, `log_message`가 표준 로거로 위임.
- **gui/panels/progress_panel.py**: 복사/과거 로그 버튼을 로그 창 하단으로 이동.
- **gui/panels/case_list_panel.py**: 제목 라벨을 `app.case_list_title_label`로 노출, 가로 스크롤 `_sync_xview(*args)` 수정.
- **services/logger_service.py**: `get_available_log_paths()` 추가 (과거 로그 파일 목록 반환).

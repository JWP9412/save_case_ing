# CHANGELOG v4.3.99 (2026-03-10)

## Refactoring & Structure

- **아키텍처 정리: MVC 및 서비스 계층 강화**
  - `batch_gui_maker.py` 제거. 메인 GUI 컨트롤러를 `gui/app_controller.py`의 `AppController` 클래스로 통합.
  - `utils/` 폴더 제거. `utils/email_manager.py`를 `services/email_manager.py`로 이동하여 비즈니스 로직을 서비스 계층으로 통합.
  - `gui/utils/google_sheet_loader.py`를 `gui/utils/google_sheet_ui.py`로 이름 변경(UI 래퍼 역할 명확화).

- **services/ 리팩토링**
  - `process_controller.py`: `tkinter`/`messagebox` 의존성 제거. 경고·안내·예·아니오는 `app.show_warning`, `app.show_info`, `app.ask_yesno`로 위임. GUI 갱신은 `app.ui_queue`를 통해서만 수행.
  - `process_controller.py`: 긴 메서드 분리. `_process_one_case`를 `_report_progress`, `_validate_captcha_input`, `_resolve_last_entry`, `_apply_sheet_correction`, `_finish_case_no_change`, `_finish_case_with_save`, `_process_result_list` 등 헬퍼로 분리. `process_all_captcha_inputs` 완료/오류 블록을 `_kill_chrome_debug_processes`, `_finish_captcha_batch_ui`, `_queue_restore_ui_after_captcha_batch`로 분리.
  - `google_sheets.py`: `save_progress_data`를 `_get_or_create_case_worksheet`, `_ensure_headers_and_remove_timestamp_rows`, `_build_result_rows_and_color_info`, `_append_empty_and_timestamp_rows` 등 private 메서드로 분리.

- **auto_runner.py MockApp 인터페이스 동기화**
  - `update_case_status(case_number, ...)`, `update_case_timestamp(case, original_index, row_count, is_auto=True)` 시그니처를 GUI 쪽과 통일.
  - `show_warning`, `show_info`, `ask_yesno`, `get_case_status_text` 등 AppController와 동일한 UI 위임 메서드 추가.
  - `services.update_history` 상단 임포트로 통일, 중복 임포트 제거.

- **GitHub 푸시 전 정리**
  - 프로젝트 전역 `__pycache__` 및 `*.pyc` 삭제.
  - 빈 `utils/` 폴더 제거.

## Technical

- **config.py**: `APP_VERSION = "4.3.99"` 업데이트.
- **gui/app_controller.py**: `show_warning`, `show_info`, `ask_yesno`, `get_case_status_text` 추가.
- **services/process_controller.py**: 주석에서 BatchProcessingGUI -> AppController/MockApp 반영.

# README v4.3.99 (2026-03-10)

## 주요 변경 사항

### 1. 아키텍처 정리 (v4.3.99)
- **메인 GUI**: `batch_gui_maker.py` 제거. `gui/app_controller.py`의 `AppController`가 메인 컨트롤러로 통합.
- **utils 폴더 제거**: `email_manager.py`를 `services/email_manager.py`로 이동. 비즈니스 로직은 모두 `services/`에 배치.
- **gui/utils**: 구글 시트 UI 래퍼를 `google_sheet_ui.py`로 이름 변경.

### 2. services 계층 개선
- **ProcessController**: Tkinter/메시지박스 의존성 제거. UI 알림은 app 위임 메서드(`show_warning`, `show_info`, `ask_yesno`) 및 `ui_queue`로만 처리.
- **긴 메서드 분리**: `_process_one_case`, `process_all_captcha_inputs`를 단일 책임 헬퍼 메서드로 분리.
- **GoogleSheetsService**: `save_progress_data` 내부를 private 헬퍼 메서드로 모듈화.

### 3. CLI(MockApp) 인터페이스 통일
- GUI와 동일한 메서드 시그니처 및 UI 위임 메서드로 ProcessController 재사용성 확보.

### 4. GitHub 푸시 전 정리
- `__pycache__` 및 `.pyc` 제거. 빈 `utils/` 폴더 제거.

---

## Technical Updates
- `APP_VERSION`: "4.3.99"
- 진입점: `main.py` -> `gui/main_window.py` -> `AppController`.
- 이메일/알림 로직: `services/email_manager.py`.

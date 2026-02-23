# CHANGELOG v4.1.2 (2026-01-28)

## Features & Improvements

- **리팩토링 및 코드 정리**
  - 사건 목록 UI를 `gui/panels/case_list_panel.py`로 분리·정리.
  - 메인 GUI 로직(`batch_gui_maker.py`) 다이어트 및 패널 조립 방식 유지.

- **프로젝트 구조 정리**
  - `utils/` 폴더 추가: 공통 유틸 모듈용 패키지. 향후 헬퍼 함수 등 배치.
  - `batch_gui_maker_v2_backup.py` 백업 파일 제거.

## Technical

- **batch_gui_maker.py**: 리팩토링으로 사건 목록 관련 UI 로직을 패널로 위임, 코드 경량화.
- **gui/panels/case_list_panel.py**: 사건 목록 패널 단일 책임으로 정리.
- **utils/**: `__init__.py` 추가, 패키지로 등록.

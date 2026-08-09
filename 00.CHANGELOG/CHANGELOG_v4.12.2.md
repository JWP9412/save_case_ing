# CHANGELOG v4.12.2

## v4.12.2 주요 변경 (2026-08-10)

### Features & Improvements

- **사건 시트 관리 드롭다운**
  - 제어 패널의 '중복 오류 제거', '기록 초기화 및 재수집', '시트-대법원 대조'를
    '사건 시트 관리' 버튼의 묶고, 클릭 시 팝업 메뉴로 실행.
  - '특정 기간 조회'는 독립 버튼으로 유지.

- **버전 업데이트 확인**
  - 제어 패널에 '버전 업데이트 확인' 버튼 추가.
  - GitHub(`JWP9412/save_case_ing`) 최신 릴리스와 로컬 `APP_VERSION` 비교.
  - Releases가 없으면 태그(tags) API로 폴백.
  - 새 버전이 있으면 릴리스/태그 페이지를 열 수 있음.

- **일반내용 표 정렬 수정**
  - 헤더·내용 열이 어긋나던 문제를 `grid` 고정 열로 수정.
  - 헤더 키 불일치 시에도 preferred 열 순서를 유지하고 값 매칭을 보강.

### 이전 버전 요약 (v4.12.1)

- Windows node.exe 콘솔 창 숨김 (`CREATE_NO_WINDOW`).

## Technical

- `config.py`: `APP_VERSION = "4.12.2"`, `BTN_TEXT_SHEET_MGMT`, `BTN_TEXT_CHECK_UPDATE`, `GITHUB_*`.
- `gui/panels/control_panel.py`: 시트 관리 메뉴, 버전 확인 버튼.
- `services/update_checker.py`: GitHub releases/latest 조회(없으면 tags 폴백)·버전 비교.
- `gui/app_controller.py`: `check_app_update()`.
- `gui/dialogs/general_info_dialog.py`: `_render_table` grid + `_cell_value_for_header`.

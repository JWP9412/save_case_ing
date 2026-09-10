# CHANGELOG v5.3.2

## v5.3.2 주요 변경 (2026-09-10)

공식 버전 흐름: **v5.3.1 → v5.3.2**

### Features & Improvements

- **한번에 여러 사건 추가하기**
  - 사건목록 관리에 일괄 추가 탭 추가.
  - 엑셀형 격자(법원·사건번호·피고·사건명 헤더 + 칸), Ctrl+V 붙여넣기, 행 추가.
  - 법원 열 드롭다운(자동완성, 기존 사건 추가와 동일 목록).
  - 선택 행 지우기 / 전체 지우기 / 목록에 넣기.
  - 빈칸·법원명 불일치·중복 사건번호는 넣지 않고 안내.

- **일반내용 뷰어 가독성**
  - 창 최소 크기 상향, 기본내용 라벨·값 줄바꿈.
  - 기본내용 좌·우 열 50:50 균등.
  - 당사자「이름」열 비중 확대, 기일표「시각」열은 좁게(표별 열 비중 분리).

### Bug Fixes

- **일괄 추가 창이 떴다 꺼지던 문제**
  - 격자 초기화 중 `pending_listbox` 미생성 상태에서 버튼 갱신 → AttributeError 수정.
  - `tk.Frame` 안 `CTkScrollbar` 조합 제거(Windows Tcl 크래시 방지).
  - `MouseWheel` `bind_all` 제거.
  - 창 열기 실패 시 메인 앱은 유지.

- **당사자내용 사이트↔앱 불일치**
  - 이름 열이 좁아 잘리던 표시 버그 수정.
  - `PageController` 당사자 표 파싱: `innerText` 우선, rowspan/colspan 논리 그리드.

### Technical

- `config.py`: `APP_VERSION = "5.3.2"`.
- `gui/dialogs/case_list_manage_dialog.py`: 일괄 격자·TkCourtAutocomplete.
- `gui/app_controller.py`: 사건목록 관리 열기 try/except.
- `gui/dialogs/general_info_dialog.py`: 열 비중·최소 크기·기본내용 grid.
- `src/PageController.js`: `parseDataTable` rowspan/`cellText`.

### 이전 버전 요약 (v5.3.1)

- CLI READY 줄 훔침 수정·숨김 필터·Node READY 선행·시작 전 고아 청소·로그 쉬운 말.

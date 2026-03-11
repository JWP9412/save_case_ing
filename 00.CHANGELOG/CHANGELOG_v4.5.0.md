# CHANGELOG v4.5.0

## 사건목록 관리

- **사건목록 관리 다이얼로그** (`gui/dialogs/case_list_manage_dialog.py`)
  - 탭: 사건 추가, 사건 수정, 사건 삭제, 숨기기, 숨김 해제.
  - 구글 시트 사건 목록에 행 추가/수정/삭제, 숨긴 사건 로컬 관리 (`data/hidden_cases.json`).
- **법원 필드**
  - 법원명 드롭다운(전체 목록) + 입력 시 자동완성(필터). Toplevel 오버레이로 목록 표시해 폼 간격 유지.
  - 입력창 오른쪽 ▼ 버튼으로 목록 열기. 입력창 길이 통일(법원 행 기준 316px).
- **폼 필드**
  - 비고/일자/내용 제거. 법원, 사건번호, 피고, 사건명만 표시.

## UI 조정

- **사건 목록 패널**
  - "사건목록 관리" 버튼 최우측 배치, 하늘색(`#5DADE2`/`#4A9FD4`).
  - "사건 목록 열 순서"(⚙) 버튼 하늘색. 열 순서 다이얼로그 창 너비 400, 버튼 크기 10% 축소.
- **숨김 처리**
  - 로드 시 숨긴 사건 필터. 필터 후 0건이면 자동으로 숨김 해제 후 전체 표시.

## 버그 수정

- **구글 시트**
  - `delete_row_by_case_number`: gspread `delete_rows(start, end)` 1-based exclusive 사용으로 삭제 오류 해결.
  - `load_case_list`: 사건번호가 숫자(int)로 올 때 `.strip()` 오류 방지(`str(raw).strip()`).
- **사건목록 관리 다이얼로그**
  - 사건번호가 int인 경우 삭제/숨기기/수정 시 `AttributeError` 방지(모든 사건번호 접근 시 `str` 변환).
- **hidden_cases 비교**
  - `_on_load_google_sheet_done`에서 사건번호 문자열 통일 후 비교.

## 버전

- `config.py`: `APP_VERSION = "4.5.0"`으로 업데이트.

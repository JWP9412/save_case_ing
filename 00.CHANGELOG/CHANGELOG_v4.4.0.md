# CHANGELOG v4.4.0

## 기능 추가

- **사건 목록 '기일' 열 추가**
  - 구글 시트의 A열 `일자`, B열 기일 정보(예: `판결선고기일(동관 제557호 법정[①번 법정출입구 이용] 14:00)`)를 읽어와 사건 목록에 별도 열로 표시.
  - `gui/panels/case_row.py`에서 정규식을 사용해 `변론기일`/`판결선고기일`과 시간을 추출하고, `기일 날짜 시간` 형식으로 렌더링.
  - `config.py`의 `COL_NAMES`, `COL_WIDTHS`, `DEFAULT_COL_ORDER`를 확장하여 '피고/사건명' 우측에 '기일' 열을 배치.

## 정렬 및 UX

- **정렬 인덱스 정리**
  - `services/sort_manager.py`에서 정렬 인덱스를 새 구조에 맞게 조정(3=기일, 4=비고, 8=자동 조회, 9=최근 업데이트).
  - `gui/utils/case_list_columns.py`에서 헤더 클릭 시 기일/비고/자동 조회/최근 업데이트 열 정렬을 지원.
  - `AppController.sort_column_index` 기본값을 최근 업데이트 열(내부 인덱스 9)로 갱신.

## 기타

- 열 개수 변경에 따라 `data/column_widths.json`, `data/column_order.json`의 길이가 `COL_NAMES`/`COL_WIDTHS`와 다르면 기존 캐시를 무시하고 기본값을 사용하도록 기존 방어 로직(`case_list_builder`, `case_list_columns`)이 그대로 동작합니다.

## 버전

- `config.py`: `APP_VERSION = "4.4.0"`으로 업데이트.


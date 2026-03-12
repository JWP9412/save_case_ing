# CHANGELOG v4.6.0

## 사건목록 관리 다이얼로그 (v4.6.0)

- **적용·확인·취소 플로우**
  - 적용: 대기 중인 변경을 일괄 반영 후 스냅샷 저장. 확인 시 "적용을 완료하시겠습니까?" 다이얼로그.
  - 확인: 적용 후 구글 시트 새로고침 및 다이얼로그 닫기(변경이 있을 때만).
  - 취소: "적용 사항을 취소하시겠습니까?" 확인 후 마지막 적용 스냅샷으로 되돌리기. X 버튼도 동일 동작.
- **버튼 상태**
  - 7개 버튼(숨기기, 숨김 해제, 사건 삭제, 변경 취소, 추가, 선택 사건 불러오기, 저장)을 선택/폼 상태에 따라 조건부 활성·비활성.

## 버그 수정 (v4.6.0)

- **사건목록 관리 다이얼로그**
  - `_on_cancel_pending_change`: `kind` 참조 전 할당 오류 수정(`to_remove` 리스트 컴프리헨션에서 `meta[i]`가 이미 `(kind, key)`인 점 반영).
- **사건 목록 패널**
  - `create_list_header` 리사이즈 람다에서 이벤트 인자 없이 호출될 때 `TypeError` 방지(`lambda e=None` 사용).
- **column_resizer**
  - `on_resize_press`, `on_resize_motion`, `on_resize_release`에서 `event is None` 시 early return.

## 버전

- `config.py`: `APP_VERSION = "4.6.0"`으로 업데이트.

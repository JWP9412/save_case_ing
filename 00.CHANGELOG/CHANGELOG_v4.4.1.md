# CHANGELOG v4.4.1

## 기일 정보 표시 개선

- **기일 정보 캐싱**
  - 기일 데이터가 개별 사건 시트에만 있어 메인 "사건 목록"에서 읽을 수 없던 문제를 해결.
  - 크롤링 완료 시 `ProcessController._extract_hearing_from_result`로 결과에서 최신 변론기일/판결선고기일 하나만 추출해 `update_history.json`의 `hearing_info` 필드에 저장.
  - 사건 목록 UI는 `update_history.json` 캐시만 읽어 기일 열에 표시. 기일 정보가 없으면 "기일 미정"으로 표기.

## 자동 조회 표기

- **변경없음 시에도 '자동 가능' 반영**
  - 최초 조회 성공 후 "변경없음"으로 끝나도 검색 로그에 기록하고 '자동 조회' 열을 "자동 가능"으로 갱신하도록 수정 (`_finish_case_no_change`, `_process_auto_case` 변경없음 분기).

## 버전

- `config.py`: `APP_VERSION = "4.4.1"`으로 업데이트.

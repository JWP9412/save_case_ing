# CHANGELOG v4.6.3

## 중복 진행내용 무한 증식 버그 수정 및 중복 오류 제거 (v4.6.3)

- **신규 데이터 필터 역순 매칭**
  - `ProcessController.filter_new_data`: 크롤링 결과를 역순 탐색해 시트 마지막 저장 내역과 일치하는 **가장 아래쪽** 행을 기준으로 신규만 저장.
  - 대법원 화면에 동일 일자·내용이 여러 행(파란/주황 등) 있을 때 정순 매칭으로 같은 기록이 반복 저장되던 문제 해결.

- **중복 오류 제거 기능**
  - 제어 패널 **「🧹 중복 오류 제거」** 버튼 추가.
  - 선택 사건의 개별 시트에서 일자·내용·결과·공시문이 모두 같은 행을 첫 번째만 남기고 삭제.
  - `GoogleSheetsService.remove_duplicate_rows_from_sheet`, `AppController.remove_duplicates_for_selected_cases`.

## 버전

- `config.py`: `APP_VERSION = "4.6.3"`으로 업데이트.

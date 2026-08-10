# CHANGELOG v4.13.0

## v4.13.0 주요 변경 (2026-08-10)

### Features & Improvements

- **기간조회 실패 재실행**
  - 기간/대조 모드에서도 실패 건에 대해 「다시 실행할까요?」확인창을 띄움.
  - 예이면 기간(또는 대조) 모드를 유지한 채 실패 건만 재실행.

- **기간조회 상태·행 색**
  - 상태: `기간조회 완료(YY.MM.DD. ~ YY.MM.DD.)` 형식으로 조회 기간 표시.
  - 성공 행 배경을 초록(`#D4EDDA`)으로 맞춤 (이전에는 노랑 `처리중`이 남음).

- **리포트 미리보기 Markdown 기본**
  - 탭 순서 Markdown → HTML, 열릴 때 Markdown 선택.

- **사건 시트 관리 ▾**
  - 드롭다운임을 알리는 ▾ 표시.

- **브라우저 Code 21 완화**
  - 프로필(userDataDir) 락을 cleanup까지 유지.
  - 레인 인덱스 = instance_N 통일, 레인 시작 stagger.

- **시트「최근 조회 일시」**
  - footer에 `업데이트 일시` 아래 `최근 조회 일시` 행 추가.
  - 기간조회·변경없음·대조에서도 조회 시각만 갱신 (`touch_last_query_time`).

### 이전 버전 요약 (v4.12.2)

- 사건 시트 관리 드롭다운, 버전 업데이트 확인, 일반내용 표 정렬.

## Technical

- `config.py`: `APP_VERSION = "4.13.0"`, `BTN_TEXT_SHEET_MGMT`에 ▾.
- `gui/utils/ui_queue_manager.py`: 성공 계열 상태 배경 초록.
- `gui/dialogs/report_preview_dialog.py`: Markdown 기본 탭.
- `services/date_utils.py`: `format_date_yy`.
- `services/process_controller.py`: 실패 재실행·프로필 락·기간 상태문구·touch 연결.
- `services/google_sheets.py`: footer 2행, `touch_last_query_time`.

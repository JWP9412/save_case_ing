# CHANGELOG v5.0.0

## v5.0.0 주요 변경 (2026-08-11)

공식 버전 흐름: **v4.12.1 → v5.0.0**  
(로컬에서만 쓰이던 4.12.2~4.14.1 표기는 공식 이력에서 제외하고 본 버전에 통합)

### Features & Improvements

- **기일 달력 (미어캣싱)**
  - 변론·감정·판결선고기일 월간 달력.
  - `hearing_events` 저장 + `hearing_info` 폴백(재조회 전에도 표시).
  - 칸 안 요약(`• 피고/사건명 종류`), 복수 시 `+n`, 하단 상세.
  - 사건목록 관리 왼쪽 「달력」 버튼.

- **지연 등록 비고**
  - 신규 시트 행 비고·로그: `(n일 지연 등록. 영업일 기준)` (토·일 제외).

- **제품명**
  - UI 제목 `APP_TITLE = 미어캣싱` (저장소/폴더명 case-ing 유지).

- **기간조회·시트**
  - 기간/대조 실패 건 재실행 확인창.
  - 상태 `기간조회 완료(YY.MM.DD. ~ …)`, 성공 행 초록.
  - 리포트 미리보기 Markdown 기본.
  - 시트 footer「최근 조회 일시」.
  - 「사건 시트 관리 ▾」드롭다운(중복 제거·초기화 재수집·대조).
  - 「버전 업데이트 확인」(GitHub releases/tags).

- **설정 창**
  - 「사건 조회 설정」탭(병렬·재시도·대기) — 메인 화면 처리 설정 단락 제거.
  - 「테마」탭(다크/라이트/시스템).
  - 버튼: 적용 / 확인 / 취소.

- **진행상황 로그**
  - Canvas 워터마크(로고 뒤 · 글자 앞).
  - 휠 스크롤·스크롤바·드래그 선택·Ctrl+C·복사, 폰트 11pt.

- **OCR·기일 표시**
  - OCR 자동 입력 후 wait 전 auto-submit(완료 버튼 없이 다음 단계).
  - 기일 열「감정기일」=「변론기일」과 동일(민트색·줄바꿈).

- **일반내용 표**
  - 헤더·내용 열 grid 정렬 수정.

- **안정성**
  - 프로필 락·레인=instance로 Chrome Code 21 완화.

### 이전 버전 요약 (v4.12.1)

- Windows `node.exe` 콘솔 창 숨김 (`CREATE_NO_WINDOW`).

## Technical

- `config.py`: `APP_VERSION = "5.0.0"`.
- `gui/dialogs/settings_dialog.py`, `hearing_calendar_dialog.py`.
- `gui/panels/progress_panel.py` (`StatusLogCanvas`), `case_row.py`, `case_list_panel.py`.
- `gui/main_window.py`: 메인 처리 설정 패널 제거.
- `services/process_controller.py`: OCR auto-submit 타이밍.
- `services/update_history.py`, `google_sheets.py`, `update_checker.py`.

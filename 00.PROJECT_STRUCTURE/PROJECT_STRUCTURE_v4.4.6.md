# 프로젝트 구조 (Project Structure) - v4.4.6

## Root Directory
- **`config.py`** (v4.4.6): 버전 상수 `APP_VERSION = "4.4.6"`. 사건 목록 컬럼 11개(기일 열 포함). THEME에 `hearing_mint` 추가.
- **`main.py`**: `--auto` 파라미터 처리 및 `run_auto_batch` 호출 분기. GUI 모드는 `gui.main_window.run_app()` 진입.
- **`auto_runner.py`**: CLI 전용 실행기. `MockApp`이 ProcessController와 동일한 인터페이스 제공.
- **`data/`**: 설정 및 이력용 JSON. `column_widths.json`/`column_order.json`은 열 개수 11 기준.
- **`logs/`**: 실행 시마다 새 로그 파일 생성 (최대 10개 유지).

## gui/ (UI)
- **`main_window.py`**: GUI 조립 및 실행. `AppController` 인스턴스 생성 및 `run()` 호출.
- **`app_controller.py`**: 메인 컨트롤러. 기본 정렬 열 `sort_column_index = 9`(최근 업데이트). `get_days_until_hearing(hearing_info)` 위임.
- **`panels/`**: ControlPanel, CaseListPanel, HeaderPanel 등.
  - **`case_row.py`**: 행 렌더링. 기일 열은 CTkTextbox로 디데이·민트색(변론/판결선고기일)·YY.MM.DD 표기·수직 가운데(grid). 법원/사건번호·피고/사건명·비고는 grid+스페이서 수직 가운데, 비고만 좌측 정렬. 최근 업데이트 열 grid 수직 가운데. 시트 버튼 아이콘만. 행 높이 90.
- **`dialogs/`**: captcha_dialog, settings_dialog, find_dialog, sheet_viewer_dialog, column_order_dialog.
- **`utils/`**: UI 전용 헬퍼.
  - `case_list_builder.py`: `label_info_1`, `label_info_2`, `label_info_4`(비고) 참조.
  - `case_list_columns.py`: 정렬 가능 열 (1,2,3,4,8,9). `sort_manager`, 열 순서/너비 로드·저장.
  - `column_resizer.py`: 표시 열 인덱스 0~10.
  - `history_ui.py`: 업데이트 기록 UI 갱신. 날짜 형식 `YY.MM.DD.\nHH:MM:SS` 적용.
  - 기타: ui_queue_manager, google_sheet_ui, search_ui, selection_manager, email_ui, captcha_ui, window_lifecycle, window_bootstrap, bind_utils.

## services/ (Business Logic)
- **`sort_manager.py`**: 정렬 키 인덱스 1,2,3(기일),4,8,9 지원.
- **`process_controller.py`**: `_extract_hearing_from_result`로 기일 추출. **`update_history.py`**: `get_days_until_hearing(hearing_info)` 추가.
- **`google_sheets.py`**, **`email_manager.py`**, **`history_manager.py`**, **`puppeteer.py`**, **`logger_service.py`**, **`search_manager.py`**, **`theme_manager.py`**: v4.3.99와 동일 역할.

## src/, gas/, 문서
- **`src/`**: Puppeteer (interactive_runner.js, PageController.js).
- **`gas/`**: SendNotificationMail.gs.
- **`00.CHANGELOG/`**, **`00.README/`**, **`00.PROJECT_STRUCTURE/`**: 버전별 문서. v4.4.6에서 기일·최근 업데이트·사건 목록 레이아웃 개선 반영.

---

## 트리 형식 (요약)

```
case-ing/
├── config.py
├── main.py
├── auto_runner.py
├── data/
├── logs/
├── src/
│   ├── interactive_runner.js
│   └── PageController.js
├── services/
│   ├── process_controller.py
│   ├── google_sheets.py
│   ├── email_manager.py
│   ├── history_manager.py
│   ├── update_history.py
│   ├── puppeteer.py
│   ├── logger_service.py
│   ├── search_manager.py
│   └── theme_manager.py
├── gui/
│   ├── main_window.py
│   ├── app_controller.py
│   ├── panels/
│   │   ├── case_list_panel.py
│   │   ├── case_row.py
│   │   └── ...
│   ├── dialogs/
│   │   ├── captcha_dialog.py
│   │   ├── settings_dialog.py
│   │   ├── find_dialog.py
│   │   ├── sheet_viewer_dialog.py
│   │   └── column_order_dialog.py
│   └── utils/
│       ├── ui_queue_manager.py
│       ├── case_list_builder.py
│       ├── history_ui.py
│       ├── column_resizer.py
│       ├── google_sheet_ui.py
│       ├── case_list_columns.py
│       └── ...
├── gas/
│   └── SendNotificationMail.gs
├── 00.CHANGELOG/
├── 00.README/
└── 00.PROJECT_STRUCTURE/
```

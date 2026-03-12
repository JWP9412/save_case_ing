# 프로젝트 구조 (Project Structure) - v4.6.2

## Root Directory
- **`config.py`** (v4.6.2): 버전 상수 `APP_VERSION = "4.6.2"`. `CASE_LIST_CACHE_FILE`(사건 목록 캐시). 사건 목록 컬럼 11개(기일 열 포함). THEME에 `hearing_mint` 추가.
- **`main.py`**: `--auto` 파라미터 처리 및 `run_auto_batch` 호출 분기. GUI 모드는 `gui.main_window.run_app()` 진입.
- **`auto_runner.py`**: CLI 전용 실행기. `MockApp`이 ProcessController와 동일한 인터페이스 제공.
- **`data/`**: 설정 및 이력용 JSON. `column_widths.json`/`column_order.json`은 열 개수 11 기준. `hidden_cases.json`(숨긴 사건). **`case_list_cache.json`**(사건 목록 캐시, 시작 시 빠른 로딩).
- **`logs/`**: 실행 시마다 새 로그 파일 생성 (최대 10개 유지).

## gui/ (UI)
- **`main_window.py`**: GUI 조립 및 실행. **F5** 바인딩으로 `gui.load_google_sheet(force_network=True)` 호출.
- **`app_controller.py`**: 메인 컨트롤러. **`run()`**: 캐시 있으면 withdraw → 캐시 로드·적용·목록 그리기 → deiconify; 없으면 after(100, load_google_sheet). `load_google_sheet(force_network=False)` 시그니처.
- **`panels/`**: ControlPanel, CaseListPanel, HeaderPanel 등.
  - **`case_list_panel.py`**: 사건 목록 헤더·리스트. 리사이즈 람다 `e=None`.
  - **`case_row.py`**: 행 렌더링. 기일 열 CTkTextbox, 법원/사건번호·피고/사건명·비고 grid, 행 높이 90.
- **`dialogs/`**: captcha_dialog, settings_dialog, find_dialog, sheet_viewer_dialog, column_order_dialog, **case_list_manage_dialog**.
  - **`case_list_manage_dialog.py`**: 사건 추가/수정/삭제/숨기기/숨김 해제. 적용·확인·취소, 7개 버튼 상태. 확인 시 `load_google_sheet(force_network=True)`.
- **`utils/`**: UI 전용 헬퍼.
  - **`google_sheet_ui.py`**: `load_case_list_cache`/`save_case_list_cache`, `_case_list_cache_path()`(프로젝트 루트 기준). `load_google_sheet(app, force_network=False)` 캐시 우선. `_apply_loaded_data_to_app`. 네트워크 성공 시 캐시 저장.
  - **`case_list_builder.py`**: 30건 이하 한 배치에 그리기(`batch_size = n_cases if n_cases <= 30 else ...`). 그 외 v4.6.0과 동일.
  - `case_list_columns.py`, `column_resizer.py`, `history_ui.py` 등: v4.6.0과 동일.
- **control_panel**: 새로고침 버튼 텍스트 "🔄 새로고침 (F5)", command `load_google_sheet(force_network=True)`.

## services/ (Business Logic)
- **`sort_manager.py`**, **`process_controller.py`**, **`google_sheets.py`**, **`email_manager.py`**, **`history_manager.py`**, **`update_history.py`**, **`puppeteer.py`**, **`logger_service.py`**, **`search_manager.py`**, **`theme_manager.py`**: v4.6.0과 동일 역할.

## src/, gas/, 문서
- **`src/`**: Puppeteer (interactive_runner.js, PageController.js).
- **`gas/`**: SendNotificationMail.gs.
- **`00.CHANGELOG/`**, **`00.README/`**, **`00.PROJECT_STRUCTURE/`**: 버전별 문서. v4.6.2에서 사건 목록 캐시·시작 시 목록 표시·UI 배치·F5 새로고침 반영.

---

## 트리 형식 (요약)

```
case-ing/
├── config.py
├── main.py
├── auto_runner.py
├── data/
│   ├── case_list_cache.json
│   ├── hidden_cases.json
│   └── ...
├── logs/
├── src/
│   ├── interactive_runner.js
│   └── PageController.js
├── services/
│   ├── process_controller.py
│   ├── google_sheets.py
│   └── ...
├── gui/
│   ├── main_window.py
│   ├── app_controller.py
│   ├── panels/
│   │   ├── case_list_panel.py
│   │   ├── case_row.py
│   │   └── ...
│   ├── dialogs/
│   │   └── case_list_manage_dialog.py
│   └── utils/
│       ├── google_sheet_ui.py
│       ├── case_list_builder.py
│       └── ...
├── gas/
│   └── SendNotificationMail.gs
├── 00.CHANGELOG/
├── 00.README/
└── 00.PROJECT_STRUCTURE/
```

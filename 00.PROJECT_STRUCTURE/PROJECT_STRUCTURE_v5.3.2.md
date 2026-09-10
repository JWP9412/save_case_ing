# 프로젝트 구조 (Project Structure) - v5.3.2

## Root Directory

- **`config.py`**: `APP_VERSION = "5.3.2"`, `PROFILE_COUNT`, OCR·캐시·스크린샷·알림메일 상수. `load_user_settings()`.
- **`main.py`**: GUI / `--auto` 진입점. 시작 시 `load_user_settings()`.
- **`auto_runner.py`**: CLI 일괄 자동 조회. `load_user_settings()` + 숨김 필터 + 시작 전 고아 Node 청소.
- **`AGENTS.md`**: 프로젝트 규칙 (진입점·설정 로드 보호 포함).
- **`requirements.txt`**: Python 의존성.

## gui/

- **`app_controller.py`**: 메인 컨트롤러. 사건목록 관리 열기 try/except.
- **`dialogs/case_list_manage_dialog.py`**: 사건 추가/수정/숨김 + **일괄 추가 격자**(TkCourtAutocomplete, 붙여넣기, 지우기).
- **`dialogs/general_info_dialog.py`**: 일반내용 뷰어. 열 비중(표별), 최소 크기, 기본내용 50:50 grid.
- **`dialogs/settings_dialog.py`**: 프로필 수, 알림 수신 메일 등.
- **`panels/progress_panel.py`**: 진행상황 로그.
- **`utils/`**: captcha_ui, google_sheet_ui, window_lifecycle 등.

## services/

- **`puppeteer.py`**: 레인 워커, 레인당 stdout 큐, IDLE drain.
- **`general_info_store.py`**: 일반내용 로컬 JSON 저장/조회.
- **`finalized_case.py`**: 종국 판별(기본내용 종국결과 칸만).
- **`process_controller/`**: case_runner, captcha_ocr, result_handler, cleanup, controller.

## src/

- **`interactive_runner.js`**: `--worker` 상주. READY 후 puppeteer 로드.
- **`PageController.js`**: 검색·진행내용 + **일반내용 추출**(`parseDataTable` rowspan/`innerText`).

## 문서

- `00.CHANGELOG/CHANGELOG_v5.3.2.md`
- `00.README/README_v5.3.2.md`
- `00.PROJECT_STRUCTURE/PROJECT_STRUCTURE_v5.3.2.md`

## 트리 형식 (요약)

```
case-ing/
├── config.py                              # 5.3.2
├── gui/
│   ├── app_controller.py                  # 관리 창 열기 보호
│   └── dialogs/
│       ├── case_list_manage_dialog.py     # 일괄 추가 격자
│       └── general_info_dialog.py         # 일반내용 표시
├── services/
│   └── general_info_store.py
└── src/
    └── PageController.js                  # 당사자 표 파싱 보강
```

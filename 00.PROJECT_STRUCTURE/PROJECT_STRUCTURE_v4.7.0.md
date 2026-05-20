# 프로젝트 구조 (Project Structure) - v4.7.0

## Root Directory
- **`config.py`** (v4.7.0): `APP_VERSION = "4.7.0"`, OAuth·캘린더 설정 상수.
- **`main.py`**, **`auto_runner.py`**, **`data/`**, **`logs/`**: 이전 버전과 동일 역할.

## gui/ (UI)
- **`app_controller.py`**: 배치 특수 작업은 `batch_actions` 모듈에 위임.
- **`utils/batch_actions.py`** (신규): 중복 제거·기록 초기화·재수집 확인 대화상자 및 플래그 설정.
- **`panels/control_panel.py`**: `dedup_btn`(중복 오류 제거), `reset_btn`(기록 초기화 및 재수집).
- **`dialogs/settings_dialog.py`**: 구글 OAuth 연동, 캘린더 켜기/끄기·이벤트 템플릿.

## services/ (Business Logic)
- **`google_oauth.py`** (신규): OAuth 2.0 로그인·토큰 저장.
- **`google_calendar.py`** (신규): 기일 캘린더 이벤트 등록.
- **`google_sheets.py`**: `get_case_worksheet_url`, `overwrite_sheet_data`, `sync_and_remove_duplicates`, A:F 명시 저장.
- **`process_controller.py`**: `_process_result_list` (일반/중복제거/초기화 통합), `_as_process_result`.
- **`email_manager.py`**: 메일 본문 시트 바로가기 URL.
- **`update_history.py`**: `clear_last_entry` (초기화 시 로컬 캐시 삭제).

## src/, gas/, 문서
- **`src/`**: Puppeteer 크롤링.
- **`00.CHANGELOG/`**, **`00.README/`**, **`00.PROJECT_STRUCTURE/`**: v4.7.0 문서 추가.

---

## 트리 형식 (요약)

```
case-ing/
├── config.py
├── services/
│   ├── google_oauth.py
│   ├── google_calendar.py
│   ├── google_sheets.py
│   ├── process_controller.py
│   └── email_manager.py
├── gui/
│   ├── app_controller.py
│   ├── utils/batch_actions.py
│   └── panels/control_panel.py   # dedup_btn, reset_btn
└── ...
```

# 프로젝트 구조 (Project Structure) - v5.0.0

## Root Directory

- **`config.py`**: `APP_VERSION = "5.0.0"`, `APP_TITLE = "미어캣싱"`, 사용자 설정·OCR·시트 상수.
- **`main.py`**: GUI / `--auto` 진입점.
- **`requirements.txt`**: Python 의존성 (customtkinter, gspread, OCR 등).

## gui/

- **`app_controller.py`**: 메인 컨트롤러.
- **`main_window.py`**: 좌·우 패널 조립 (처리 설정 패널 호출 제거).
- **`dialogs/settings_dialog.py`**: 구글 시트 / 사건 조회 설정 / 테마 / 자동화 / 일반.
- **`dialogs/hearing_calendar_dialog.py`**: 기일 달력(폴백·칸 요약).
- **`panels/progress_panel.py`**: `StatusLogCanvas` 워터마크·스크롤·선택.
- **`panels/case_row.py`**: 기일 열(변론·감정·판결 민트·줄바꿈).
- **`panels/case_list_panel.py`**: 달력 버튼, 사건목록 관리.
- **`panels/control_panel.py`**: 수집·시트 관리·기간 조회·버전 확인.
- **`utils/ui_queue_manager.py`**: 로그·상태 갱신 큐.

## services/

- **`process_controller.py`**: 차로제 조회, OCR fill, auto-submit.
- **`update_history.py`**: hearing_info / hearing_events.
- **`google_sheets.py`**, **`update_checker.py`**, **`puppeteer.py`** 등.

## src/

- Puppeteer(Node) 자동화 (`PageController.js`, `index.js`).

## 문서

- `00.CHANGELOG/CHANGELOG_v5.0.0.md`
- `00.README/README_v5.0.0.md`
- 본 파일
- 루트 `README.md` (상세 사용법)

## 트리 형식 (요약)

```
case-ing/
├── config.py                         # 5.0.0
├── main.py
├── requirements.txt
├── gui/
│   ├── app_controller.py
│   ├── main_window.py
│   ├── dialogs/settings_dialog.py    # 사건 조회 설정 · 테마
│   ├── dialogs/hearing_calendar_dialog.py
│   └── panels/progress_panel.py      # StatusLogCanvas
├── services/process_controller.py    # OCR auto-submit
├── src/                              # Puppeteer
└── 00.CHANGELOG / 00.README / ...
```

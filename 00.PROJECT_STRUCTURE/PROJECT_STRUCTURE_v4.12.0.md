# 프로젝트 구조 (Project Structure) - v4.12.0

## Root Directory
- **`config.py`** (v4.12.0): `APP_VERSION = "4.12.0"`, `GENERAL_INFO_FILE`, `APP_ICON_*`, `UI_USE_EMOJI`.
- **`CaseIng.spec`**, **`실행.bat`**, **`assets/app_icon.*`**.
- **`main.py`**, **`auto_runner.py`**.

## gui/
- **`dialogs/general_info_dialog.py`**: 일반내용 뷰어 (기본내용·기일·서류·당사자·대리인).
- **`panels/case_row.py`**: 피고/사건명 칸 돋보기(보기) 버튼.
- **`app_controller.py`**: `_open_general_info`.
- **`utils/window_bootstrap.py`**, **`utils/glyphs.py`**, **`utils/batch_actions.py`**.

## services/
- **`general_info_store.py`**: `data/general_info.json` 저장/조회.
- **`puppeteer.py`**: `last_general_info` 보관함.
- **`process_controller.py`**: `_persist_general_info`.
- **`email_manager.py`**, **`period_report.py`**, **`sheet_compare.py`**.

## src/
- **`PageController.js`**: `extractGeneralInfo` (진행내용 탭 클릭 직전).
- **`interactive_runner.js`**: JSON `generalInfo` 필드.

## scripts/
- **`inspect_general_info_dom.js`**: 일반내용 DOM 실측 결론 메모.

## 문서
- **`00.CHANGELOG/CHANGELOG_v4.12.0.md`**, **`00.README/README_v4.12.0.md`**, 본 파일.

## 트리 형식 (요약)

```
case-ing/
├── config.py                         # 4.12.0, GENERAL_INFO_FILE
├── data/general_info.json            # 런타임 생성 (gitignore)
├── gui/dialogs/general_info_dialog.py
├── gui/panels/case_row.py            # 돋보기 버튼
├── services/general_info_store.py
├── src/PageController.js             # extractGeneralInfo
└── ...
```

# 프로젝트 구조 (Project Structure) - v4.12.1

## Root Directory
- **`config.py`** (v4.12.1): `APP_VERSION = "4.12.1"`, `GENERAL_INFO_FILE`, `APP_ICON_*`.
- **`CaseIng.spec`**, **`실행.bat`**, **`assets/app_icon.*`**.

## services/
- **`puppeteer.py`**: Windows에서 `CREATE_NO_WINDOW`로 node.exe 콘솔 숨김.
- **`general_info_store.py`**: 일반내용 로컬 저장/조회.
- **`process_controller.py`**: `_persist_general_info`.

## gui/
- **`dialogs/general_info_dialog.py`**: 일반내용 뷰어.
- **`panels/case_row.py`**: 피고/사건명 칸 보기 버튼.

## src/
- **`PageController.js`**: `extractGeneralInfo`.
- **`interactive_runner.js`**: JSON `generalInfo` 필드.

## 문서
- **`00.CHANGELOG/CHANGELOG_v4.12.1.md`**, **`00.README/README_v4.12.1.md`**, 본 파일.

## 트리 형식 (요약)

```
case-ing/
├── config.py                 # 4.12.1
├── services/puppeteer.py     # CREATE_NO_WINDOW (Windows)
└── ...
```

# 프로젝트 구조 (Project Structure) - v4.12.2

## Root Directory
- **`config.py`** (v4.12.2): `APP_VERSION`, `BTN_TEXT_SHEET_MGMT`, `BTN_TEXT_CHECK_UPDATE`, `GITHUB_REPO` / `GITHUB_RELEASES_*`.

## gui/
- **`panels/control_panel.py`**: 사건 시트 관리(tk.Menu), 버전 업데이트 확인 버튼.
- **`dialogs/general_info_dialog.py`**: 일반내용 표 grid 정렬.
- **`app_controller.py`**: `check_app_update()`.

## services/
- **`update_checker.py`**: GitHub 최신 릴리스 조회·버전 비교.
- **`puppeteer.py`**: Windows `CREATE_NO_WINDOW`.
- **`general_info_store.py`**: 일반내용 로컬 저장.

## 문서
- **`00.CHANGELOG/CHANGELOG_v4.12.2.md`**, **`00.README/README_v4.12.2.md`**, 본 파일.

## 트리 형식 (요약)

```
case-ing/
├── config.py                      # 4.12.2, GITHUB_*, BTN_TEXT_SHEET_MGMT
├── services/update_checker.py
├── gui/panels/control_panel.py    # 시트 관리 드롭다운, 버전 확인
├── gui/dialogs/general_info_dialog.py
└── ...
```

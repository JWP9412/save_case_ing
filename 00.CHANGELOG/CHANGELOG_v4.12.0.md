# CHANGELOG v4.12.0

## v4.12.0 주요 변경 (2026-08-07)

### Features & Improvements

- **일반내용 돋보기 뷰어**
  - 사건 조회 시 대법원 '일반내용' 화면(기본내용·최근기일·최근 제출서류·당사자·대리인)을
    진행내용 탭 클릭 직전에 함께 수집해 `data/general_info.json`에 저장.
  - 사건 목록 '피고/사건명' 칸 아래쪽에 돋보기(보기) 버튼 추가.
  - 클릭 시 스크롤 가능한 일반내용 창에서 사진1~3과 같은 구성을 표시.
  - 창 안 '당사자·대리인 내용 변경시 클릭' 버튼으로 해당 사건만 재조회해 최신화 가능.
  - 일반내용 수집 실패해도 기존 진행내용 크롤링·시트 저장은 중단되지 않음.

### 이전 버전 요약 (v4.11.0)

- 앱 아이콘(미어캣+저울), 창·exe 아이콘, `실행.bat`.

## Technical

- `config.py`: `APP_VERSION = "4.12.0"`, `GENERAL_INFO_FILE`.
- `services/general_info_store.py`: 일반내용 로컬 저장/조회.
- `src/PageController.js`: `extractGeneralInfo`, 진행내용 탭 클릭 직전 호출.
- `src/interactive_runner.js`: 결과 JSON에 `generalInfo` 필드.
- `services/puppeteer.py`: `last_general_info` 보관함 (반환 타입 유지).
- `services/process_controller.py`: `_persist_general_info`.
- `gui/dialogs/general_info_dialog.py`: 일반내용 뷰어.
- `gui/panels/case_row.py`: 피고/사건명 칸 돋보기 버튼.
- `gui/app_controller.py`: `_open_general_info`.
- `scripts/inspect_general_info_dom.js`: DOM 실측 결론 메모.

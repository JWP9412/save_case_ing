# Project rules

## 빠른 작업 (필수)
- **파일 위치는 먼저** `00.PROJECT_STRUCTURE/` 최신 `PROJECT_STRUCTURE_v*.md`를 본다. 넓게 탐색·전수 grep은 그다음이다.
- 단순 지시(버전 번호만 바꾸기 등)는 최소 파일만 고치고, 과잉 검증·자동 커밋/푸시 하지 않는다.
- 상세: `.cursor/rules/fast-work-project-structure.mdc`

## 버전 릴리스
버전을 올릴 때는 반드시 [docs/VERSION_RELEASE_CHECKLIST.md](docs/VERSION_RELEASE_CHECKLIST.md)의 체크리스트를 따른다. config.py의 APP_VERSION 수정, 00.CHANGELOG/CHANGELOG_vX.Y.Z.md, 00.README/README_vX.Y.Z.md, 00.PROJECT_STRUCTURE/PROJECT_STRUCTURE_vX.Y.Z.md 신규 작성, 루트 README.md 갱신을 모두 수행한 뒤 커밋·푸시한다.
(번호만 고치라는 짧은 지시와 정식 릴리스는 구분한다. 짧은 지시에는 체크리스트 전체·커밋/푸시를 자동으로 붙이지 않는다.)

## 진입점·설정 로드 (절대 함부로 건드리지 말 것)
사용자 설정은 `data/user_settings.json`에 있고, 메모리 반영은 **`config.load_user_settings()`** 뿐이다.

- **보호 대상:** `main.py`, `auto_runner.py`의 설정 로드·메일·시트 ID·GAS URL 경로. `config.NOTIFICATION_EMAIL_ADDRESS`, `GOOGLE_SHEET_ID`, `NOTIFICATION_GAS_WEBAPP_URL` 등 `USER_SETTINGS_OVERRIDABLE` 관련 기본값/로드 로직.
- **금지:** 사용자 지시 없이 위 경로를 삭제·이동·우회하거나, `load_user_settings()` 호출을 빼거나, CLI/GUI 한쪽만 설정을 무시하게 바꾸지 않는다.
- **버그 대응 순서:** “설정이 없다/메일이 없다/시트 ID가 비었다”면 **먼저** 해당 진입점에 `load_user_settings()`가 있는지, `user_settings.json`에 값이 있는지 확인한다. 설정 UI·메일 발송 로직을 넓게 리팩터링하지 않는다.
- **주니어 참고:** GUI는 `main.py`에서, CLI 자동조회는 `auto_runner.py`에서 각각 `load_user_settings()`를 호출해야 한다. 한쪽만 호출하면 설정 창에 저장해도 CLI에서 빈 값으로 보인다.

# CHANGELOG v4.9.0

## v4.9.0 주요 변경 (2026-07-21)

### Features & Improvements

- **캡차 OCR 자동인식·자동제출**
  - EasyOCR → Tesseract 폴백으로 캡차 숫자를 읽고, 신뢰도가 충분하면 입력칸을 채운 뒤 「캡차 입력 완료」까지 자동 진행.
  - OCR 중 입력칸 잠금, 상태 문구(`OCR 인식 중` / `OCR 자동입력중` / `수동입력 필요`).
  - 캡차 불일치 시 자동 재인식·재제출(최대 `OCR_MAX_AUTO_RETRY`), 실패 시 수동 입력으로 폴백.
  - `config.py`: `OCR_ENABLED`, `OCR_AUTO_SUBMIT`, `OCR_DIGIT_COUNT`, `OCR_CONFIDENCE_THRESHOLD`, `OCR_MAX_AUTO_RETRY`.

- **Windows 포터블 배포**
  - PyInstaller onedir로 `CaseIng.exe` 생성, Node·Chrome·`src`·`node_modules`·`ocr_export`를 폴더에 동봉.
  - `BASE_DIR` / `path_from_base`로 exe 옆 상대경로 동작. Puppeteer는 동봉 `runtime/node/node.exe` 우선 사용.
  - `.puppeteerrc.cjs` + `runtime/puppeteer`로 Chrome을 홈 캐시가 아닌 배포 폴더에 고정.
  - 빌드: `scripts/build_portable.ps1`, 스펙: `CaseIng.spec`.
  - 사용자 안내: `docs/DEPLOY_WINDOWS.md`, `docs/PORTABLE_LAYOUT.md`, `docs/README_PORTABLE.txt` → 배포 시 `README.TXT`.

- **포터블·인증 사용자 안내 보강**
  - `client_secret.json` 발급·배치 절차를 비전공자용으로 상세 기술.
  - 구글 시트 준비(사건 목록 탭·헤더·시트 ID·편집 권한·설정 입력)를 README에 추가.
  - `api/certification/README.md`에 시트 준비 필수 단계 요약.

### 이전 버전 요약 (v4.8.0)

- 구글 시트 429 완화(저장 직렬화·1회 읽기·batch 통합), 신규 건수 오판·알림메일 50,000자 수정.

## Technical

- `config.py`: `APP_VERSION = "4.9.0"`, `get_base_dir` / `BASE_DIR` / `path_from_base`, `OCR_*` 상수.
- `ocr_export/`: `captcha_ocr.py` (EasyOCR+Tesseract), (선택) CNN 관련 파일.
- `services/captcha_ocr_service.py`: 앱 연동 래퍼, import 실패 시 graceful 폴백.
- `services/process_controller.py`: OCR 웨이브·자동 제출·수동 폴백.
- `gui/utils/captcha_ui.py`, `gui/app_controller.py`: 입력 잠금·OCR 텍스트 설정(스레드 안전).
- `services/puppeteer.py`: 동봉 Node 경로, `cwd=BASE_DIR`.
- `services/email_manager.py`, `services/logger_service.py`, `gui/utils/google_sheet_ui.py`: `path_from_base` 적용.
- `CaseIng.spec`, `scripts/build_portable.ps1`, `requirements-build.txt`, `.puppeteerrc.cjs`.
- `docs/DEPLOY_WINDOWS.md`, `docs/PORTABLE_LAYOUT.md`, `docs/README_PORTABLE.txt`, `api/certification/README.md`.
- `.gitignore`: `case-ing-portable/`, `runtime/puppeteer/`, `client_secret.json` 등.

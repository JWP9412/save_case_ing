# README v4.9.0

## 주요 변경 사항

### 1. 캡차 OCR 자동인식·자동제출 (v4.9.0)
- EasyOCR로 숫자를 읽고, 실패 시 Tesseract로 보완.
- 신뢰도 통과 시 입력칸을 채우고 「캡차 입력 완료」까지 자동.
- OCR 중에는 입력칸을 잠그고, 상태 문구로 진행 상황을 표시.
- 실패·불일치 시 자동 재시도 후 수동 입력으로 전환.

### 2. Windows 포터블 배포 (v4.9.0)
- `CaseIng.exe` 더블클릭으로 실행 (Python·Node 별도 설치 불필요).
- Node·Chrome·Puppeteer 스크립트·OCR을 폴더에 동봉.
- 빌드: `powershell -ExecutionPolicy Bypass -File scripts/build_portable.ps1`
- 사용자 안내: 배포 폴더 `README.TXT`, `docs/DEPLOY_WINDOWS.md`

### 3. 사용자 안내 보강 (v4.9.0)
- `client_secret.json` 발급·배치, 구글 시트(사건 목록·시트 ID·편집 권한·설정) 절차를 상세화.

### 4. 구글 시트 429 완화 (v4.8.0)
- 저장 직렬화, 사건당 1회 읽기, 서식 API 1회 전송, jitter 재시도.
- 조회 실패 시 신규 건수 오판 방지, 알림메일 50,000자 truncate.

### 5. 구글 캘린더·OAuth·시트·메일 (v4.7.0)
- 캘린더 자동 등록, 설정창 OAuth, 시트 열 밀림 수정, 메일 바로가기.

### 6. 기록 초기화·재수집·중복 제거 (v4.7.0)
- 초기화·재수집, 중복 오류 제거.

---

## Technical Updates
- `APP_VERSION`: "4.9.0"
- 신규: `services/captcha_ocr_service.py`, `ocr_export/`, `CaseIng.spec`, `scripts/build_portable.ps1`, `.puppeteerrc.cjs`
- 수정: `config.py` (BASE_DIR·OCR_*), `process_controller.py`, `captcha_ui.py`, `puppeteer.py`, 경로 관련 서비스/GUI
- 문서: `docs/DEPLOY_WINDOWS.md`, `docs/PORTABLE_LAYOUT.md`, `docs/README_PORTABLE.txt`, `api/certification/README.md`

## 설정 참고
- OCR 끄기: `OCR_ENABLED = False` (수동 입력만).
- 자동 제출만 끄기: `OCR_AUTO_SUBMIT = False` (채우기만, 완료는 수동).
- 포터블: `api/certification/client_secret.json` 배치 후 설정에서 구글 연동·시트 ID 입력.

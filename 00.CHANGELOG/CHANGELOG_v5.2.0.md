# CHANGELOG v5.2.0

## v5.2.0 주요 변경 (2026-09-08)

공식 버전 흐름: **v5.1.1 → v5.2.0**

### Bug Fixes

- **실패 건수 집계 오류**
  - 파도(wave)마다 `completed`/`failed`가 0으로 리셋되어, 실제 실패 2건인데 팝업에 1건만 나오던 문제 수정.
  - 배치 단위 `_batch_completed` / `_batch_failed` / `_batch_failed_cases`로 누적.
  - 재실행 팝업은 위젯 텍스트 대신 실패 집합을 우선 사용 (UI 큐 타이밍 누락 방지).

- **진행내용 탭 클릭이 “성공으로 오판”**
  - `progressTab.click()` 후 무조건 `tabClicked=true` 하던 로직을, 탭 바디 표시 확인 → 실패 시 JS click → 텍스트 전략 순으로 변경.
  - 그리드 대기 타임아웃 18초 → 8초.

- **그리드 실패 후 무의미한 재시도**
  - Node가 종료된 뒤에도 같은 프로세스에 재전송하던 경로 제거.
  - 프로세스가 죽었으면 `capture_captcha_image`부터 브라우저 재기동 후 OCR·재시도.
  - 디버그 스크린샷을 절대 경로로 저장하고, body 판정 예외에도 스크린샷이 남도록 순서 변경.

- **Tesseract 가짜 신뢰도 1.00**
  - 자릿수만 맞으면 `confidence=1.0`을 넣던 하드코딩 제거.
  - `image_to_data` 문자별 conf 평균/최솟값 사용. 임계값 미달이면 수동 폴백.
  - EasyOCR·Tesseract 결과가 일치하면 신뢰도 가산.

### Features & Improvements

- **Chrome 재사용 (레인 워커)**
  - 사건마다 Node+Chrome을 띄우던 구조를 레인(프로필)당 워커 1개 상주로 변경.
  - `PROFILE_COUNT`와 레인 수를 1:1로 묶어 Chrome 기동 횟수를 사건 수 → 레인 수로 축소.

- **설정: 브라우저 프로필 수**
  - 「사건 조회 설정」에 `PROFILE_COUNT` 입력란·추천 도움말 추가 (사건 수/메모리 기반).
  - 값 변경 시 병렬 처리 수를 동일하게 맞춤.

- **속도**
  - EasyOCR 앱 시작 시 백그라운드 워밍업.
  - 사이트 접속 `domcontentloaded` + 폰트/미디어/스타일·광고 차단 (이미지 유지).
  - OCR 전처리: 3배+NlMeans → 2배+medianBlur.
  - 레인 시작 지연 1.0초 → 0.3초.

- **메모리**
  - Chrome 저메모리 launch args, EasyOCR 유휴 언로드, 프로필 캐시·스크린샷 자동 정리.
  - 사건 완료 후 캡차 PhotoImage 참조 해제.

- **캡차 학습 데이터 수집**
  - 성공/실패 캡차를 `data/captcha_dataset/`에 자동 저장 (`services/captcha_dataset.py`).
  - 학습 스크립트는 데이터 축적 후 별도 진행.

### Technical

- `config.py`: `APP_VERSION = "5.2.0"`, `PROFILE_COUNT`, OCR/캐시/스크린샷 관련 상수.
- `src/interactive_runner.js`: `--worker` 모드.
- `services/puppeteer.py`: `lane_workers` / `shutdown_all_workers`.
- `services/profile_maintenance.py`, `services/captcha_dataset.py` 신설.
- `ocr_export/captcha_ocr.py`: 실제 Tesseract conf, preprocess 경량화, `unload_easyocr`.
- `src/PageController.js`: 탭 전환 검증, 리소스 차단, 그리드 8초.

### 이전 버전 요약 (v5.1.1)

- 시작 버튼 `@staticmethod` 오류, 진행상황 스크롤바·전체 복사 수정.

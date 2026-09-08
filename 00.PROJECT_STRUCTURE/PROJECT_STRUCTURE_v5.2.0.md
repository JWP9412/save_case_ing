# 프로젝트 구조 (Project Structure) - v5.2.0

## Root Directory

- **`config.py`**: `APP_VERSION = "5.2.0"`, `PROFILE_COUNT`, OCR·캐시·스크린샷 상수.
- **`main.py`**: GUI / `--auto` 진입점.
- **`auto_runner.py`**: CLI 일괄 자동 조회.
- **`requirements.txt`**: Python 의존성.

## gui/

- **`app_controller.py`**: 메인 컨트롤러 (EasyOCR 워밍업, 메모리 경고).
- **`dialogs/settings_dialog.py`**: `PROFILE_COUNT` 설정·추천 도움말.
- **`utils/captcha_ui.py`**: 캡차 표시, `release_captcha_image_memory`.
- **`utils/window_bootstrap.py`**, **`google_sheet_ui.py`**: 병렬도=프로필 수 동기화.

## services/

- **`puppeteer.py`**: 레인 워커(`--worker`) · Chrome 재사용.
- **`captcha_dataset.py`**: 캡차 학습 데이터 수집.
- **`profile_maintenance.py`**: 프로필 캐시·스크린샷 정리.
- **`captcha_ocr_service.py`**: OCR 래퍼, 워밍업/언로드.
- **`process_controller/`**
  - `case_runner.py` — 배치 집계, 재시도 재기동, 프로필=레인
  - `captcha_ocr.py`, `result_handler.py`, `cleanup.py`, `controller.py`

## src/

- **`interactive_runner.js`**: 레거시 1건 모드 + `--worker` 상주 모드.
- **`PageController.js`**: 탭 전환 검증, 리소스 차단, 그리드 8초.

## ocr_export/

- **`captcha_ocr.py`**: EasyOCR + Tesseract(실제 conf), preprocess 경량화, `unload_easyocr`.

## 문서

- `00.CHANGELOG/CHANGELOG_v5.2.0.md`
- `00.README/README_v5.2.0.md`
- `00.PROJECT_STRUCTURE/PROJECT_STRUCTURE_v5.2.0.md`

## 트리 형식 (요약)

```
case-ing/
├── config.py                         # 5.2.0, PROFILE_COUNT
├── services/
│   ├── puppeteer.py                  # lane_workers
│   ├── captcha_dataset.py
│   ├── profile_maintenance.py
│   └── process_controller/case_runner.py
├── src/
│   ├── interactive_runner.js         # --worker
│   └── PageController.js
└── ocr_export/captcha_ocr.py
```

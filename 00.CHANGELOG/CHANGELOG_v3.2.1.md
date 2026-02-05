# CHANGELOG v3.2.1 (2026-02-05)

## 🛠️ Bug Fixes & Improvements
- **GUI (BatchProcessingGUI)**: `tk.BooleanVar` 초기화 시점을 `create_window`로 이동하여 `RuntimeError: no default root window` 해결
- **Configuration**: 앱 버전 및 타이틀 정보를 `config.py`로 집중 관리하도록 구조 개선 (하드코딩 제거)
- **Scraping (PageController)**: 검색 결과 로딩 대기 로직 강화 및 그리드 탐색 실패 시 예비(fallback) 전략 추가로 안정성 향상
- **Services**: Google Sheets 및 Puppeteer 서비스 모듈의 로깅 및 처리 효율 개선

# CHANGELOG v4.2.2 (2026-03-05)

## Features & Improvements

- **구조적 리팩터링 (batch_gui_maker.py 다이어트)**
  - `batch_gui_maker.py`의 비대해진 로직을 `services/process_controller.py`로 대폭 이전.
  - 사건 처리 로직(병렬 실행, 캡차 처리, 결과 저장 등)을 서비스 레이어로 분리하여 유지보수성 향상.
  - 파일 I/O 및 히스토리 관리 기능을 `services/history_manager.py`로 독립시켜 책임 분리.

- **안정성 및 오류 처리 강화**
  - 병렬 처리 중 발생할 수 있는 UI 프리징 및 "응답없음" 현상 개선을 위한 스레드 안전성 강화.
  - 실패한 사건들에 대해 사용자에게 알림창을 띄우고 실패 건만 재실행할 수 있는 기능 추가.
  - `HistoryManager` 간의 명칭 충돌 문제 해결 및 로그 로딩 로직 안정화.

- **UI/UX 개선**
  - 제어 패널 내 버튼들의 크기 및 높이를 통일하여 시각적 일관성 확보.
  - 설정 버튼 및 이메일 발송 버튼의 활성화 상태에 따른 색상 구분 명확화.
  - 과거 로그 보기 창에 '복사' 버튼을 추가하여 로그 데이터 활용 편의성 증대.

- **프로젝트 구조 정리**
  - 불필요한 테스트 파일(Cypress 등) 및 미사용 코드 제거.
  - `package.json` 정리 및 주석 추가를 통한 프로젝트 명세 명확화.

## Technical

- **config.py**: `APP_VERSION = "4.2.2"` 업데이트.
- **batch_gui_maker.py**: 대규모 코드 분리 및 `ProcessController`, `HistoryManager` 위임 구조 도입.
- **services/process_controller.py**: 핵심 비즈니스 로직(사건 조회/처리/저장) 통합 관리.
- **services/history_manager.py**: 검색 기록 및 상태 이력 파일 관리 전담.
- **services/logger_service.py**: 실행 시마다 개별 로그 파일 생성 및 최대 10개 유지 관리.

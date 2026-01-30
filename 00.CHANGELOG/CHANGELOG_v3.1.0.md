# Changelog

All notable changes to this project will be documented in this file.

## [v3.1.0] - 2026-01-30

### 🚀 New Features (신규 기능)
- **대화형 러너 (Interactive Runner)**: `src/interactive_runner.js`를 도입하여 브라우저 프로세스를 종료하지 않고 지속적으로 유지합니다. 이를 통해 재연결 시 캡차 이미지가 변경되는 고질적인 문제를 해결했습니다.
- **스마트 스킵 (Smart Skip)**: 'CLICK' 입력을 지원하여, 캡차 입력을 건너뛰고 최근 검색 기록을 클릭하는 기능을 강화했습니다. 쿠키 지속성을 통해 재검색 효율을 높였습니다.

### 🛠️ Improvements & Fixes (개선 및 수정)
- **아키텍처 변경**: Python(`batch_gui_maker.py`)과 Node.js(`interactive_runner.js`) 간의 통신 방식을 표준 입출력(stdin/stdout) 기반으로 변경하여 제어권을 강화했습니다.
- **데이터 추출 안정화**: '진행내용' 탭을 찾지 못하는 문제를 해결하기 위해 ID 기반 검색과 텍스트 기반 검색을 병행하는 **이중 전략(Dual Strategy)**을 적용했습니다.
- **입력 인식 오류 해결**: 사건번호와 당사자명 입력 시 WebSquare 프레임워크가 값을 인식하지 못하는 문제를 해결하기 위해, 검색 직전 입력 필드를 다시 클릭하고 포커스를 주는 로직을 추가했습니다.
- **페이지 새로고침 방지**: 검색 버튼 클릭 시 Enter 키 입력을 제거하고 순수 JS 클릭을 사용하여 폼 중복 제출로 인한 페이지 새로고침 현상을 수정했습니다.
- **브라우저 안정성**: `--disable-dev-shm-usage` 및 `--disable-gpu` 옵션을 추가하여 `net::ERR_SOCKET_NOT_CONNECTED` 오류 및 검은 화면 현상을 해결했습니다.
- **알림창 자동 처리**: "검색 결과가 없습니다" 등의 알림창이 뜰 경우 자동으로 닫아 프로세스가 멈추지 않도록 개선했습니다.

## [v3.0.0] - 2026-01-28

### ✨ Major Features
- **Python GUI 도입**: `batch_gui_maker.py`를 통해 사용자 친화적인 GUI 환경 제공.
- **Puppeteer 마이그레이션**: 기존 Cypress 기반 코드를 Puppeteer로 완전히 전환하여 병렬 처리 및 제어 능력 향상.
- **구글 시트 연동 강화**: 사건 목록 자동 로드 및 결과 자동 저장 기능 구현.

### 🐛 Bug Fixes
- 초기 UI 렌더링 문제 및 컬럼 정렬 수정.
- 대법원 사이트 접속 불안정성 개선.

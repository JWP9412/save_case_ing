# CHANGELOG v4.3.0 (2026-03-08)

## Features & Improvements

- **CLI 자동 실행(Auto-run) 안정화**
  - CLI 모드(`--auto`) 실행 시 브라우저 기동 단계(캡차 로딩)가 누락되어 즉시 실패하던 문제 해결.
  - GUI와 동일하게 '브라우저 기동 -> 스마트 스킵(CLICK) 명령 전송'의 2단계 프로세스를 거치도록 `process_cli_auto_case` 메서드 도입.
  - `MockApp`에 `profile_locks`를 추가하여 CLI 환경에서도 안전한 다중 프로필(인스턴스) 접근 제어 지원.

- **이메일 하단 '조회 결과 요약' 디자인 전면 개편**
  - 기존의 단순 쉼표 나열 방식에서 벗어나 **[사건번호 | 피고/사건명]** 구조의 명확한 테이블 형식 도입.
  - 결과 상태별(성공, 성공(변경없음), 실패, 캡차 재시도 안 함)로 개별 표를 생성하여 가독성 대폭 향상.
  - 메일 데이터 구조를 딕셔너리 리스트 형태로 고도화하여 상세 정보 표시 지원.

- **안정성 강화**
  - CLI 모드 처리 완료 후 브라우저 프로세스가 정상적으로 종료되도록 클린업 로직 보완.
  - `ProcessController` 내 CLI 전용 예외 처리 및 로깅 강화.

## Technical

- **config.py**: `APP_VERSION = "4.3.0"` 업데이트.
- **auto_runner.py**: `MockApp` 구조 개선 및 CLI 전용 워커 로직(`process_cli_auto_case` 호출) 반영.
- **services/process_controller.py**: CLI 전용 자동 처리 메서드 추가 및 결과 저장 로직 고도화.
- **utils/email_manager.py**: 요약 결과 생성을 위한 `_build_run_result_footer` 테이블 렌더링 로직 도입.

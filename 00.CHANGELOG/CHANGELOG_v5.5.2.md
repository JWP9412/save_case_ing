# CHANGELOG v5.5.2

## v5.5.2 주요 변경 (2026-10-02)

공식 버전 흐름: **v5.5.1 → v5.5.2**

### Features & Improvements

- **결과 변경만 있는 사건은 메일 맨 뒤**
  - 최신 업데이트가 있는 사건이 먼저 옵니다. 그 안에서는 기록이 많은 순입니다.
  - 업데이트 없이 결과 변경만 있는 사건은 행이 더 많아도 맨 뒤로 갑니다.

### Technical

- `config.py`: `APP_VERSION = "5.5.2"`.
- `services/email_manager.py`: `_group_notification_cases` 정렬. 업데이트 있는 사건 우선, 결과변경만 있는 사건은 뒤.
- `scripts/test_mail_split.py`: 결과변경만 있는 사건이 뒤에 오는지 확인.

### 이전 버전 요약 (v5.5.1)

- 같은 카드에서 결과 변경 구역만 하늘색, 경계에 파란색 구분선.

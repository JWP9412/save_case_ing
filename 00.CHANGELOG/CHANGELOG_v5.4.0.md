# CHANGELOG v5.4.0

## v5.4.0 주요 변경 (2026-09-29)

공식 버전 흐름: **v5.3.3 → v5.4.0**

### Features & Improvements

- **알림메일 카드형 HTML**
  - 사건(시트)별로 흰 카드 UI. 일자/내용/결과 **시트 글자색 유지**.
  - 바로가기 링크·조회 결과 요약도 같은 카드 스타일.

- **알림메일 분할 발송**
  - 구글 시트 셀 한도(약 5만 자)를 넘으면 **여러 행(=여러 메일)** 으로 나눠 기록.
  - 카드/행 경계를 지켜 태그 중간에서 잘리지 않음.
  - 한 사건이 길면 `(이어짐 N)` 카드로 분할.
  - **성공/실패 등 조회 요약은 마지막 메일**에 포함.
  - 본문 배너: `CASE-ING NOTIFICATION · 메일 N/M`.

- **안전 절단 폴백**
  - 한도를 넘는 경우 깨진 `<td style=...` 조각을 남기지 않고,
    `(이하 N자 생략 — …)` 안내만 표시.

### Technical

- `config.py`: `APP_VERSION = "5.4.0"`.
- `services/email_manager.py`: `get_summary_html_parts`, `safe_trim_html`, 카드 패킹.
- `services/google_sheets.py`: `append_notification_mails`.
- `gui/utils/email_ui.py`, `auto_runner.py`, `gui/dialogs/report_preview_dialog.py` 연동.
- `scripts/test_mail_split.py`: 분할·안전절단 스모크 테스트.

### 이전 버전 요약 (v5.3.3)

- 버전 업데이트 확인이 Release와 태그 중 높은 쪽을 사용.
- 릴리스 시 `gh release create` 체크리스트.

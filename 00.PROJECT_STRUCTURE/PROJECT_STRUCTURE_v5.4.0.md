# 프로젝트 구조 (Project Structure) - v5.4.0

## Root Directory

- **`config.py`**: `APP_VERSION = "5.4.0"`, `GOOGLE_SHEET_CELL_MAX_CHARS`(알림메일 셀 한도).
- **`auto_runner.py`**: CLI 종료 시 `get_summary_html_parts` → `append_notification_mails`.

## services/

- **`email_manager.py`**: 미발송 누적·카드형 HTML.
  - `get_summary_html_parts()`: 한도 내 여러 HTML 파트.
  - `safe_trim_html()`: 깨진 태그 없는 안전 절단.
  - `_pack_mail_parts` / 카드 행 분할(`이어짐 N`).
- **`google_sheets.py`**: `append_notification_mails` — 알림메일 시트에 여러 `대기` 행 추가.

## gui/

- **`utils/email_ui.py`**: 「모든 사건 메일 발송」→ 분할 기록.
- **`dialogs/report_preview_dialog.py`**: 미리보기 발송 시 한도·안전절단 적용.

## gas/

- **`SendNotificationMail.gs`**: `대기` 행마다 발송 (변경 없음, 복수 행 = 복수 메일).

## scripts/

- **`test_mail_split.py`**: 분할·요약 위치·safe_trim 스모크 테스트.

## 문서

- `00.CHANGELOG/CHANGELOG_v5.4.0.md`
- `00.README/README_v5.4.0.md`
- `00.PROJECT_STRUCTURE/PROJECT_STRUCTURE_v5.4.0.md`

## 트리 형식 (요약)

```
case-ing/
├── config.py                              # 5.4.0
├── auto_runner.py                         # 분할 메일 기록
├── services/email_manager.py              # parts + safe_trim
├── services/google_sheets.py              # append_notification_mails
├── gui/utils/email_ui.py
├── gas/SendNotificationMail.gs
└── scripts/test_mail_split.py
```

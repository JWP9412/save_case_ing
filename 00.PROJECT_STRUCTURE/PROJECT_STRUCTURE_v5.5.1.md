# 프로젝트 구조 (Project Structure) - v5.5.1

## Root Directory

- **`config.py`**: `APP_VERSION = "5.5.1"`, `GOOGLE_SHEET_CELL_MAX_CHARS`(알림메일 셀 한도).
- **`auto_runner.py`**: CLI 종료 시 `get_summary_html_parts` → `append_notification_mails`.

## services/

- **`email_manager.py`**: 미발송 누적·사건 카드 HTML.
  - `get_summary_html_parts()`: 기록 많은 사건부터, 한도 내 여러 HTML 파트.
  - `_render_combined_case_card()`: 한 사건의 업데이트(흰색)+결과변경(하늘색)을 카드 하나. 경계선 `#7EB6D9`.
  - `_group_notification_cases()`: 시트명으로 묶고 행 수 내림차순.
  - `safe_trim_html()`: 깨진 태그 없는 안전 절단.
  - `_pack_mail_parts`: 사건 덩어리를 한 통에 최대한 채움. 한도 초과 시 `(이어짐 N)`.
- **`google_sheets.py`**: `append_notification_mails` — 알림메일 시트에 여러 `대기` 행 + E열 메일제목. 일시는 RAW.

## gui/

- **`utils/email_ui.py`**: 「모든 사건 메일 발송」→ 분할 기록.
- **`dialogs/report_preview_dialog.py`**: 미리보기 발송 시 한도·안전절단 적용.

## gas/

- **`SendNotificationMail.gs`**: `대기` 행마다 발송. E열 메일제목이 있으면 그 제목, 없으면 `(n/N)`과 `yyyy-MM-dd HH:mm:ss` 일시로 제목을 만듦. (v5.5.1에서 변경 없음)

## scripts/

- **`test_mail_split.py`**: 짧은 사건 1통·긴 사건 이어짐·결과변경 배경색·safe_trim 스모크 테스트.

## 문서

- `00.CHANGELOG/CHANGELOG_v5.5.1.md`
- `00.README/README_v5.5.1.md`
- `00.PROJECT_STRUCTURE/PROJECT_STRUCTURE_v5.5.1.md`

## 트리 형식 (요약)

```
case-ing/
├── config.py                              # 5.5.1
├── auto_runner.py                         # 분할 메일 기록
├── services/email_manager.py              # 사건 카드 + 결과변경 하늘색
├── services/google_sheets.py              # append_notification_mails (E열 제목)
├── gui/utils/email_ui.py
├── gas/SendNotificationMail.gs            # 제목 (1/N), 일시 포맷
└── scripts/test_mail_split.py
```

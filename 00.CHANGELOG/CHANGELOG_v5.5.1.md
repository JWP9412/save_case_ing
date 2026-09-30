# CHANGELOG v5.5.1

## v5.5.1 주요 변경 (2026-10-01)

공식 버전 흐름: **v5.5.0 → v5.5.1**

### Features & Improvements

- **결과 변경 구역 배경**
  - 같은 사건 카드 안에서 최신 업데이트는 흰색, **결과 변경만 하늘색**(`#E8F4FC`)입니다.
  - 두 구역이 만나면 경계에 **파란색 구분선**(`#7EB6D9`)을 긋습니다.
  - 시트에서 온 글자색은 그대로 둡니다.

### Technical

- `config.py`: `APP_VERSION = "5.5.1"`.
- `services/email_manager.py`: `_render_combined_case_card` 결과 변경 칸 배경·경계선, 표 셀 배경.
- `scripts/test_mail_split.py`: 하늘색·구분선 색이 본문에 있는지 확인.

### 이전 버전 요약 (v5.5.0)

- 알림메일을 사건 카드 하나로 묶고, 긴 기록 우선, 메일 제목 `(1/N)`.

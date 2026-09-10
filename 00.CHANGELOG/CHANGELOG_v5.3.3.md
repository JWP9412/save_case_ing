# CHANGELOG v5.3.3

## v5.3.3 주요 변경 (2026-09-10)

공식 버전 흐름: **v5.3.2 → v5.3.3**

### Bug Fixes

- **버전 업데이트 확인이 오래된 Release만 보던 문제**
  - `/releases/latest`만 보면 태그만 올린 v5.3.x가 무시되고 v5.1.1이 '최신'으로 나옴.
  - Release 최신과 Tags 최신 중 **버전 번호가 더 높은 쪽**을 사용하도록 수정.

### Technical

- `config.py`: `APP_VERSION = "5.3.3"`.
- `services/update_checker.py`: `fetch_latest_release()`가 releases+tags 비교.
- `docs/VERSION_RELEASE_CHECKLIST.md`: `gh release create` 항목 추가.
- GitHub: v5.3.2·v5.3.3 Release 게시.

### 이전 버전 요약 (v5.3.2)

- 일괄 사건 추가 격자·일괄 창 크래시 수정·당사자 표시/파싱·일반내용 가독성.

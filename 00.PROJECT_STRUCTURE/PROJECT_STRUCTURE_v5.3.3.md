# 프로젝트 구조 (Project Structure) - v5.3.3

## Root Directory

- **`config.py`**: `APP_VERSION = "5.3.3"`, `GITHUB_REPO` / `GITHUB_RELEASES_LATEST_URL` / `GITHUB_TAGS_URL`.
- **`docs/VERSION_RELEASE_CHECKLIST.md`**: 버전 올리기 체크리스트 (**`gh release create` 포함**).

## services/

- **`update_checker.py`**: 버전 확인. **Release 최신과 Tags 최신 중 높은 쪽**을 remote로 사용.

## gui/

- **`app_controller.py`**: `check_app_update()` → `update_checker.check_for_update()`.
- **`panels/control_panel.py`**: 「버전 업데이트 확인」버튼.

## 문서

- `00.CHANGELOG/CHANGELOG_v5.3.3.md`
- `00.README/README_v5.3.3.md`
- `00.PROJECT_STRUCTURE/PROJECT_STRUCTURE_v5.3.3.md`

## 트리 형식 (요약)

```
case-ing/
├── config.py                         # 5.3.3
├── docs/VERSION_RELEASE_CHECKLIST.md # gh release create
└── services/update_checker.py        # max(releases, tags)
```

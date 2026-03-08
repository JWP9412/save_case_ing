# 버전 올릴 때 체크리스트

새 버전(예: v4.1.3)을 릴리스할 때 아래 순서대로 진행한다.

| 순서 | 작업 |
|------|------|
| 1 | [config.py](../config.py)에서 `APP_VERSION` 수정 (예: `"4.1.3"`) |
| 2 | `00.CHANGELOG/CHANGELOG_vX.Y.Z.md` 신규 작성 (이전 버전 복사 후 변경 이력 반영) |
| 3 | `00.README/README_vX.Y.Z.md` 신규 작성 (이전 버전 복사 후 버전·특징·구조·링크 수정) |
| 4 | `00.PROJECT_STRUCTURE/PROJECT_STRUCTURE_vX.Y.Z.md` 신규 작성 (이전 버전 복사 후 구조 반영) |
| 5 | 루트 [README.md](../README.md) 버전·현재 버전 특징·프로젝트 구조·개발 히스토리·상세 변경 이력 링크 갱신 |
| 6 | 커밋 후 GitHub 푸시 (필요 시 태그 `vX.Y.Z`) |

## 문서 형식 참고

- **CHANGELOG**: `00.CHANGELOG/CHANGELOG_v4.1.2.md` 형식 (날짜, Features & Improvements, Technical).
- **README(버전별)**: `00.README/README_v4.1.2.md` 형식. 프로젝트 구조 트리에 `utils/` 등 실제 디렉터리 반영.
- **PROJECT_STRUCTURE**: `00.PROJECT_STRUCTURE/PROJECT_STRUCTURE_v4.1.2.md` 형식. Root, src/, services/, gui/, utils/ 등 설명.

최신 버전 문서를 복사한 뒤 버전 번호와 변경 내용만 수정하면 된다.

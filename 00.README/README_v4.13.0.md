# case-ing README (v4.13.0)

대법원 나의 사건 조회 자동화 시스템 (Puppeteer + Python GUI) - v4.13.0

## 이 버전에서 달라진 점

1. **기간조회 실패 재실행** — 실패 건만 기간 모드로 다시 돌릴 수 있음.
2. **상태·행 색** — `기간조회 완료(기간)` 표시, 성공 행 초록.
3. **미리보기 Markdown 기본** — 탭 순서 MD → HTML.
4. **시트관리 ▾** — 드롭다운 표시.
5. **Code 21 완화** — 프로필 락·레인=instance 통일.
6. **최근 조회 일시** — 구글 시트 footer에 마지막 조회 시각.

## 실행

```bash
python main.py
python main.py --auto
```

또는 프로젝트 루트 `실행.bat` / `CaseIng.lnk`.

상세 구조·이력은 루트 `README.md` 및 `00.*` 문서를 참고하세요.

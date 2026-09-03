# 미어캣싱 README (v5.1.1)

대법원 나의 사건 조회 자동화 시스템 (Puppeteer + Python GUI) - v5.1.1  
제품 UI 명칭: **미어캣싱** (저장소/폴더명 case-ing 유지)

공식 버전: **v5.1.0 → v5.1.1**

## 이 버전에서 달라진 점 (요약)

1. **시작 버튼 오류 수정** — 「사건 기록 수집 실행」 눌렀을 때 `missing 1 required positional argument: 'cases'` 예외 해결.
2. **진행상황 스크롤바** — 좁은 패널에서도 오른쪽 스크롤바가 보이게 수정.
3. **「전체 복사」** — 복사 버튼이 로그 전체를 복사하도록 수정 (한 줄만 복사되던 문제).

## 실행

```bash
python main.py
python main.py --auto
```

사용법·설치·FAQ는 루트 [`README.md`](../README.md)에 자세히 적어 두었습니다.

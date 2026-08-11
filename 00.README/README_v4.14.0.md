# 미어캣싱 README (v4.14.0)

대법원 나의 사건 조회 자동화 시스템 (Puppeteer + Python GUI) - v4.14.0  
제품 UI 명칭: **미어캣싱** (저장소/폴더명 case-ing 유지)

## 이 버전에서 달라진 점

1. **지연 등록 비고** — 신규 시트 행에 `(n일 지연 등록. 영업일 기준)` (토·일 제외, 1일+).
2. **기일 달력** — 제어 패널 「기일 달력」으로 변론·감정·판결 월간 보기 (앱 안 창).
3. **hearing_events** — 조회 성공 시 `update_history`에 기일 목록 저장.
4. **APP_TITLE** — 창 제목 `미어캣싱`.

## 실행

```bash
python main.py
python main.py --auto
```

또는 프로젝트 루트 `실행.bat` / `CaseIng.lnk`.

상세 구조·이력은 루트 `README.md` 및 `00.*` 문서를 참고하세요.

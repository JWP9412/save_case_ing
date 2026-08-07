# case-ing README (v4.11.0)

대법원 나의 사건 조회 자동화 시스템 (Puppeteer + Python GUI) - v4.11.0

## 이 버전에서 달라진 점

1. **앱 아이콘**
   - 미어캣 + 저울(+ 보노보노식 식은땀) 공식 아이콘.
   - 창·작업표시줄·exe(`CaseIng.spec`)에 `assets/app_icon.ico` 적용.
   - 간편 실행: `실행.bat` 또는 `CaseIng.lnk`(아이콘 지정 바로가기).

2. **v4.10.0에서 이어진 기능**
   - 특정 기간 조회, 시트-대법원 대조, 메일 요약 누적(전체 사건), UI 이모지 정리.

## 실행

```bash
python main.py
python main.py --auto
```

또는 프로젝트 루트 `실행.bat` / `CaseIng.lnk`.

상세 구조·이력은 루트 `README.md` 및 `00.*` 문서를 참고하세요.

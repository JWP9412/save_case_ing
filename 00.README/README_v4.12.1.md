# case-ing README (v4.12.1)

대법원 나의 사건 조회 자동화 시스템 (Puppeteer + Python GUI) - v4.12.1

## 이 버전에서 달라진 점

1. **Windows node.exe 콘솔 창 숨김**
   - 사건 조회 시 작업표시줄에 쌓이던 `node.exe` 창이 더 이상 열리지 않음.
   - 조회·캡차·일반내용 기능은 그대로.

2. **v4.12.0에서 이어진 기능**
   - 일반내용 돋보기 뷰어, 앱 아이콘, 기간 조회, 시트 대조.

## 실행

```bash
python main.py
python main.py --auto
```

또는 프로젝트 루트 `실행.bat` / `CaseIng.lnk`.

상세 구조·이력은 루트 `README.md` 및 `00.*` 문서를 참고하세요.

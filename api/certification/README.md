# 구글 시트 연동 설정

## 서비스 계정 키 파일 설정

구글 시트 연동을 위해서는 서비스 계정 키 파일이 필요합니다.

### 1. 구글 클라우드 콘솔에서 설정

1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 프로젝트 선택 또는 새 프로젝트 생성
3. "API 및 서비스" → "사용 설정된 API" → "Google Sheets API" 활성화
4. "API 및 서비스" → "사용자 인증 정보" → "사용자 인증 정보 만들기" → "서비스 계정"
5. 서비스 계정 생성 후 "키" 탭에서 "키 추가" → "JSON" 선택
6. 다운로드된 JSON 파일을 `service-account.json`으로 이름 변경
7. 이 폴더(`api/certification/`)에 저장

### 2. 구글 시트 공유 설정

1. 구글 시트 열기
2. "공유" 버튼 클릭
3. 서비스 계정 이메일 주소 추가 (JSON 파일의 `client_email` 값)
4. "편집자" 권한 부여

### 3. 스프레드시트 ID 확인

구글 시트 URL에서 스프레드시트 ID를 확인:
```
https://docs.google.com/spreadsheets/d/[SPREADSHEET_ID]/edit
```

현재 설정된 ID: `1ShaDTz4pj8SRWvf3ahcVI-gStYK-dFSBPsS6BnDOFzU`

### 4. 테스트

설정 완료 후 다음 명령으로 테스트:
```bash
py puppeteer-to-sheets.py --all
```


# 구글 시트/캘린더 연동 설정

## 1) 앱 내 Google 연동(OAuth, 권장)

최종 사용자가 앱에서 "Google 계정 연동" 버튼만 눌러 사용하려면 OAuth 클라이언트가 필요합니다.

### 1-1. 구글 클라우드 콘솔

1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 프로젝트 선택 또는 새 프로젝트 생성
3. "API 및 서비스" → "사용 설정된 API"에서 아래 API 활성화
   - Google Sheets API
   - Google Drive API
   - Google Calendar API
4. "API 및 서비스" → "사용자 인증 정보" → "사용자 인증 정보 만들기" → "OAuth 클라이언트 ID"
5. 애플리케이션 유형: "데스크톱 앱"
6. 다운로드된 JSON 파일을 `client_secret.json`으로 저장
7. 프로젝트의 `api/certification/client_secret.json`에 배치

### 1-2. 앱 설정

- `config.py` 기본값
  - `GOOGLE_AUTH_MODE = "oauth"`
  - `GOOGLE_OAUTH_CLIENT_SECRET_FILE = "./api/certification/client_secret.json"`
- 최초 실행 또는 설정 창에서 "Google 계정 연동" 버튼을 누르면 브라우저 로그인 후
  `data/google_user_token.json`에 사용자 토큰이 저장됩니다.

## 2) 서비스 계정(레거시/고급, 선택)

OAuth 대신 서비스 계정을 계속 쓸 경우:

1. "사용자 인증 정보 만들기" → "서비스 계정"
2. 서비스 계정 키(JSON) 다운로드
3. 파일명을 `service-account.json`으로 저장
4. `api/certification/service-account.json`에 배치
5. 사용할 구글 시트에 서비스 계정 이메일(`client_email`)을 편집자로 공유
6. 캘린더도 사용할 경우, 대상 캘린더를 해당 서비스 계정 이메일에 공유

## 3) 스프레드시트/캘린더 값

- 스프레드시트 ID 확인:
  `https://docs.google.com/spreadsheets/d/[SPREADSHEET_ID]/edit`
- 기본 캘린더 ID:
  - OAuth 사용자 계정: `primary`
  - 서비스 계정 공유 캘린더: 캘린더 설정의 캘린더 ID 사용


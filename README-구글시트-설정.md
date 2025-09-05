# 🚀 Case-ing 구글시트 자동화 설정 가이드

## 📊 구글시트 준비

### 1. 구글시트 생성
```
A열: 법원명 (예: 서울중앙지방법원)
B열: 사건번호 (예: 2024가단1234)  
C열: 당사자명 (예: 김철수)
D열: (빈 열)
E열: 결과 (자동 입력됨)
F열: 스크린샷 경로 (자동 입력됨)
```

### 2. 구글 API 설정

1. **Google Cloud Console 접속**
   - https://console.cloud.google.com/

2. **새 프로젝트 생성**
   - 프로젝트명: case-ing-automation

3. **Google Sheets API 활성화**
   - API 및 서비스 > 라이브러리
   - "Google Sheets API" 검색 후 사용 설정

4. **서비스 계정 생성**
   - IAM 및 관리 > 서비스 계정
   - 서비스 계정 만들기
   - 역할: 편집자

5. **키 파일 다운로드**
   - 서비스 계정 클릭 > 키 탭
   - 키 추가 > JSON 다운로드
   - `google-service-key.json`로 이름 변경

## 🔧 파일 설정

### 1. 키 파일 배치
```
case-ing/
├── google-service-key.json  ← 여기에 배치
├── cypress.config.js
└── ...
```

### 2. 구글시트 공유
- 구글시트를 서비스 계정 이메일과 공유
- 편집 권한 부여

### 3. 시트 ID 설정
cypress.config.js의 spreadsheetId 값을 변경:
```javascript
const spreadsheetId = 'YOUR_GOOGLE_SHEET_ID';
```

## 🚀 실행

```bash
# 구글시트 기반 자동화 실행
npx cypress run --spec "cypress/e2e/final-case-ing.cy.js"
```

## 📋 결과 확인

- E열: 검색 결과 (성공/실패)
- F열: 스크린샷 파일 경로
- screenshots/ 폴더에 이미지 저장됨

## ⚠️ 주의사항

1. **서비스 키 파일** 절대 GitHub에 업로드 금지
2. **시트 권한** 서비스 계정과 공유 필수
3. **API 할당량** 하루 100회 제한 확인
4. **캐차** 수동 입력 필요시 일시정지

## 🔍 문제 해결

### 인증 오류
- 서비스 키 파일 경로 확인
- 시트 공유 권한 확인

### API 오류  
- Google Sheets API 활성화 확인
- 할당량 초과 여부 확인

### 데이터 없음
- 시트 범위 확인 (A2:D100)
- 빈 행 제외 로직 확인

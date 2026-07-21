# Windows 포터블 배포 안내 (사용자용)

이 프로그램은 **폴더 하나**를 받아 `CaseIng.exe`를 더블클릭해 실행합니다.  
(Python·Node를 따로 설치할 필요 없음 — 폴더 안에 포함)

---

## 1. 준비

1. 배포 zip을 원하는 위치에 **압축 해제**합니다.  
   예: `C:\Apps\case-ing-portable\`
2. 폴더 안에 `CaseIng.exe` 와 `runtime\`, `src\`, `node_modules\` 가 있는지 확인합니다.

---

## 2. 구글 연동 파일 넣기

1. `api\certification\` 폴더를 엽니다.
2. `client_secret.json` 을 넣습니다.  
   (없으면 README.md / 배포자에게 요청)
3. **첫 실행** 후 프로그램 **설정**에서 구글 계정 연동(로그인)을 한 번 합니다.  
   → `data\google_user_token.json` 이 자동 생성됩니다.
4. 사용할 **구글 시트 ID**가 맞는지 설정에서 확인합니다.  
   (시트를 열 수 있는 구글 계정으로 로그인해야 합니다.)

---

## 3. 실행

1. `CaseIng.exe` 더블클릭
2. 사건 목록이 보이면 정상입니다.
3. 사건 조회 → 캡차 이미지가 뜨면 OCR이 숫자를 읽고 자동 제출을 시도합니다.

### 상태 문구 (참고)

| 표시 | 의미 |
|------|------|
| OCR 인식 중 | 숫자 읽는 중 (입력칸 잠금) |
| OCR 자동입력중 | 숫자 채움, 곧 자동 완료 |
| 수동입력 필요 | OCR 실패 — 직접 입력 후 「캡차 입력 완료」 |

---

## 4. OCR·용량·첫 실행

- **EasyOCR**이 포함되어 있습니다. **첫 실행** 시 모델 준비로 **수십 초~수분** 걸릴 수 있고, **인터넷**이 필요할 수 있습니다.
- **Tesseract**는 선택입니다. 없어도 EasyOCR만으로 동작합니다.
- 폴더 용량은 **수백 MB ~ 약 1GB**일 수 있습니다 (브라우저 자동화 + OCR).

OCR을 끄려면(소스/설정 가능 시) `OCR_ENABLED` 설정을 끄면 예전처럼 수동 입력만 합니다.

---

## 5. 문제 해결

| 증상 | 확인 |
|------|------|
| exe가 안 뜸 | Windows Defender/백신 차단 여부, zip을 완전히 해제했는지 |
| 캡차/브라우저 오류 | `runtime\node\node.exe`, `runtime\puppeteer\chrome\`, `src\`, `node_modules\` 존재 여부 |
| 시트 오류 | `client_secret.json`, 구글 로그인, 시트 공유 권한 |
| OCR 실패 | 로그의 수동입력 안내 → 직접 입력 후 완료 |

개발자용 폴더 구조: `docs\PORTABLE_LAYOUT.md`

---

## 6. 개발자: 포터블 다시 만들기

빌드 PC에서 (프로젝트 루트):

```powershell
pip install -r requirements.txt
pip install pyinstaller
npm install
powershell -ExecutionPolicy Bypass -File scripts\build_portable.ps1
```

결과: `case-ing-portable\`  
이 폴더를 zip으로 묶어 배포하면 됩니다.

### 클린 폴더 검증 체크리스트

- [ ] `CaseIng.exe` 더블클릭 → GUI 기동
- [ ] 설정 → 구글 연동
- [ ] 사건 목록 로드
- [ ] 캡차 1건: Node 동봉 경로로 이미지 로드
- [ ] OCR on: 자동입력 / 실패 시 수동 폴백

# 📂 프로젝트 구조 (Project Structure)

이 파일은 case-ing 프로젝트의 전체 폴더 및 파일 구조를 설명합니다.

**최종 업데이트**: 2025-11-13

---

## 📊 전체 구조 (Tree View)

```
case-ing/
│
├── 📄 README.md                    ⭐ 전체 프로젝트 가이드
├── 📄 CHANGELOG.md                 ⭐ 변경 이력
├── 📄 PROJECT_STRUCTURE.md         ⭐ 이 파일 (프로젝트 구조 설명)
│
├── 📄 batch_gui_maker.py           🚀 메인 GUI 프로그램 (실행 파일)
├── 📄 gui_maker.py                 📦 GUI 컴포넌트 (CaptchaGUI 클래스)
│
├── 📄 package.json                 📦 Node.js 패키지 설정
├── 📄 package-lock.json            🔒 Node.js 패키지 잠금 파일
├── 📄 requirements.txt             📦 Python 패키지 설정
│
├── 📄 update_history.json          💾 로컬 업데이트 기록
│
├── 📁 api/                         🔐 API 및 인증 설정
│   └── certification/
│       ├── GOOGLE_AUTH_SETUP.md    📖 구글 인증 설정 가이드
│       └── service-account.json    🔑 구글 서비스 계정 키 (중요!)
│
├── 📁 src/                         🤖 Puppeteer 자동화 코드
│   ├── index.js                    🚀 메인 자동화 스크립트
│   ├── single-case-captcha.js      📸 캡차 이미지 캡처 전용
│   ├── BrowserManager.js           🌐 브라우저 인스턴스 관리
│   ├── PageController.js           📄 페이지 자동화 로직
│   └── ParallelProcessor.js        ⚡ 병렬 처리 오케스트레이션
│
├── 📁 screenshots/                 🖼️ 캡차 이미지 저장소
│   └── (147개의 PNG 파일)          캡처된 캡차 이미지들
│
├── 📁 results/                     💾 처리 결과 저장소
│   └── (62개의 JSON 파일)          사건별 처리 결과 데이터
│
├── 📁 puppeteer-backup/            💿 백업 코드 (참고용)
│   ├── BrowserManager.js           이전 버전 브라우저 매니저
│   ├── index.js                    이전 버전 메인 스크립트
│   ├── PageController.js           이전 버전 페이지 컨트롤러
│   ├── ParallelProcessor.js        이전 버전 병렬 처리기
│   ├── parallel-cases.test.js      병렬 처리 테스트 (참고)
│   ├── single-case.test.js         단일 사건 테스트 (참고)
│   └── src/                        (빈 폴더)
│
└── 📁 node_modules/                📦 Node.js 패키지 설치 폴더 (자동 생성)
```

---

## 📝 파일 설명 (File Descriptions)

### 🌟 핵심 실행 파일

| 파일 | 설명 | 실행 방법 |
|------|------|-----------|
| `batch_gui_maker.py` | 메인 GUI 프로그램 | `python batch_gui_maker.py` |
| `gui_maker.py` | GUI 컴포넌트 클래스 | (import로 사용) |

### 📚 문서 파일

| 파일 | 내용 | 중요도 |
|------|------|--------|
| `README.md` | 전체 프로젝트 가이드, 설치 및 사용법 | ⭐⭐⭐⭐⭐ |
| `CHANGELOG.md` | 버전별 변경 이력 | ⭐⭐⭐⭐ |
| `PROJECT_STRUCTURE.md` | 프로젝트 구조 설명 (이 파일) | ⭐⭐⭐ |
| `api/certification/GOOGLE_AUTH_SETUP.md` | 구글 인증 설정 가이드 | ⭐⭐⭐⭐ |

### ⚙️ 설정 파일

| 파일 | 용도 | 편집 필요? |
|------|------|-----------|
| `package.json` | Node.js 패키지 설정 | ❌ 자동 관리 |
| `package-lock.json` | Node.js 패키지 버전 잠금 | ❌ 자동 관리 |
| `requirements.txt` | Python 패키지 설정 | ❌ 자동 관리 |
| `update_history.json` | 업데이트 기록 | ❌ 프로그램이 관리 |

### 🔐 인증 파일

| 파일 | 내용 | 보안 중요도 |
|------|------|-----------|
| `api/certification/service-account.json` | 구글 서비스 계정 키 | 🔒 **매우 중요!** |

**⚠️ 주의**: `service-account.json`은 절대 공유하거나 GitHub에 업로드하면 안 됩니다!

---

## 🗂️ 폴더 설명 (Folder Descriptions)

### 📁 `src/` - Puppeteer 자동화 코드

**용도**: Node.js 기반 Puppeteer 자동화 스크립트

| 파일 | 역할 | 호출 방식 |
|------|------|-----------|
| `index.js` | 메인 자동화 로직 | `node src/index.js [옵션]` |
| `single-case-captcha.js` | 캡차 이미지만 캡처 | `node src/single-case-captcha.js [사건번호]` |
| `BrowserManager.js` | 브라우저 인스턴스 관리 | (모듈로 import) |
| `PageController.js` | 페이지 자동화 로직 | (모듈로 import) |
| `ParallelProcessor.js` | 병렬 처리 관리 | (모듈로 import) |

**특징**:
- ✅ 다중 브라우저 인스턴스 관리
- ✅ 브라우저 재연결 (WebSocket)
- ✅ 진행내용 데이터 자동 추출
- ✅ 자동 브라우저 종료

---

### 📁 `screenshots/` - 캡차 이미지 저장소

**용도**: 캡처된 캡차 이미지 저장

**파일명 형식**:
```
{사건번호}-{날짜}T{시간}-captcha.png
예) 2023가합10019-2025-11-13T05-51-19-captcha.png
```

**파일 개수**: 147개 (2025-11-13 기준)

**관리**:
- 🔄 프로그램이 자동으로 생성
- 🗑️ 오래된 파일은 수동으로 삭제 가능
- 📦 최신 파일은 디버깅용으로 보관 권장

---

### 📁 `results/` - 처리 결과 저장소

**용도**: 사건별 처리 결과 JSON 저장

**파일명 형식**:
```
case_result_{사건번호}_{날짜시간}.json
예) case_result_2023가합10019_20251113_055119.json
```

**파일 개수**: 62개 (2025-11-13 기준)

**내용**:
- 사건 정보 (사건번호, 피고, 법원 등)
- 진행내용 데이터 (일자, 내용, 결과, 공시문)
- 처리 메타데이터 (처리 시간, 브라우저 ID 등)

**관리**:
- 🔄 프로그램이 자동으로 생성
- 💾 백업용으로 보관 권장
- 🗑️ 용량이 부족하면 오래된 파일 삭제 가능

---

### 📁 `api/certification/` - 구글 API 인증

**용도**: 구글 시트 연동을 위한 인증 파일

| 파일 | 역할 | 필수 여부 |
|------|------|-----------|
| `service-account.json` | 구글 서비스 계정 키 | ✅ **필수** |
| `GOOGLE_AUTH_SETUP.md` | 인증 설정 가이드 | 📖 참고용 |

**설정 방법**:
1. 구글 클라우드 콘솔에서 서비스 계정 생성
2. JSON 키 다운로드
3. `service-account.json`으로 저장
4. 구글 시트에 서비스 계정 이메일 추가 (편집자 권한)

자세한 내용은 [`GOOGLE_AUTH_SETUP.md`](api/certification/GOOGLE_AUTH_SETUP.md) 참조

---

### 📁 `puppeteer-backup/` - 백업 코드

**용도**: 이전 버전 코드 백업 (참고 및 복구용)

**내용**:
- 이전 버전의 JavaScript 파일들
- 테스트 파일 (참고용)

**관리**:
- 🔒 수정하지 말 것
- 💾 복구가 필요할 때 참고
- 🗑️ 확신이 있으면 삭제 가능 (하지만 보관 권장)

---

### 📁 `node_modules/` - Node.js 패키지

**용도**: npm으로 설치된 Node.js 패키지들

**관리**:
- ❌ 수동으로 편집하지 말 것
- 🔄 `npm install`로 자동 생성
- 🗑️ 삭제 후 `npm install`로 재설치 가능
- 📦 Git에 업로드하지 말 것 (`.gitignore`에 포함)

---

## 📊 용량 현황 (Storage Usage)

| 폴더/파일 | 파일 개수 | 예상 용량 | 정리 가능? |
|-----------|-----------|-----------|-----------|
| `screenshots/` | 147개 PNG | ~300-500 KB | ✅ 오래된 파일 |
| `results/` | 62개 JSON | ~1-2 MB | ✅ 백업 후 |
| `node_modules/` | 수천 개 | ~200-500 MB | ❌ 필수 |
| `puppeteer-backup/` | ~10개 | ~100 KB | 🤔 확신 시 |

---

## 🔒 보안 주의사항

### 절대 공유하면 안 되는 파일:

1. ❌ `api/certification/service-account.json`
   - 구글 서비스 계정 키
   - GitHub, 이메일 등 어디에도 공유 금지

2. ❌ `update_history.json`
   - 사건 정보 포함 가능
   - 개인정보 보호

3. ❌ `results/*.json`
   - 사건 진행내용 포함
   - 개인정보 보호

4. ❌ `screenshots/*.png`
   - 캡차 이미지 (사건번호 포함)
   - 개인정보 보호

### `.gitignore`에 포함되어야 할 항목:

```gitignore
# 인증 파일
api/certification/service-account.json

# 데이터 파일
update_history.json
results/
screenshots/

# Node.js
node_modules/
package-lock.json

# Python
__pycache__/
*.pyc
```

---

## 🚀 프로그램 실행 순서

### 1️⃣ 최초 설정 (한 번만)

```bash
# 1. Node.js 패키지 설치
npm install

# 2. Python 패키지 설치
pip install -r requirements.txt

# 3. 구글 인증 설정
# api/certification/service-account.json 파일 생성
# (GOOGLE_AUTH_SETUP.md 참조)
```

### 2️⃣ 프로그램 실행

```bash
# 메인 GUI 실행
python batch_gui_maker.py
```

### 3️⃣ GUI에서 작업

1. 구글 시트 로드
2. 사건 선택
3. 캡차 이미지 로드
4. 캡차 입력
5. 자동 처리 시작

---

## 📞 문의 및 지원

- **GitHub 이슈**: https://github.com/JWP9412/save_case_ing/issues
- **원본 프로젝트**: https://github.com/iicdii/case-ing

---

## 📝 관련 문서

- [README.md](README.md) - 전체 프로젝트 가이드
- [CHANGELOG.md](CHANGELOG.md) - 변경 이력
- [api/certification/GOOGLE_AUTH_SETUP.md](api/certification/GOOGLE_AUTH_SETUP.md) - 구글 인증 설정

---

*최종 업데이트: 2025-11-13*


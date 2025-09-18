# Cypress → Puppeteer 마이그레이션 계획

## 🎯 목표
- 다중 브라우저 창을 이용한 병렬 처리
- 기존 Cypress 기능 100% 호환
- 성능 향상 및 메모리 효율성 개선

## 📁 새로운 프로젝트 구조
```
puppeteer-automation/
├── src/
│   ├── browser/
│   │   ├── BrowserManager.js      # 브라우저 인스턴스 관리
│   │   ├── PageController.js      # 페이지 자동화 로직
│   │   └── ScreenshotManager.js   # 스크린샷 관리
│   ├── captcha/
│   │   ├── CaptchaHandler.js      # 캡차 처리 로직
│   │   └── PythonBridge.js        # Python GUI 연동
│   ├── data/
│   │   ├── CaseProcessor.js       # 사건 데이터 처리
│   │   └── ProgressExtractor.js   # 진행내용 추출
│   └── utils/
│       ├── Logger.js              # 로깅 유틸리티
│       └── FileManager.js         # 파일 관리
├── config/
│   ├── browser.config.js          # 브라우저 설정
│   └── automation.config.js       # 자동화 설정
├── tests/
│   ├── single-case.test.js        # 단일 사건 테스트
│   └── parallel-cases.test.js     # 병렬 처리 테스트
└── package.json
```

## 🔧 핵심 기능 구현 계획

### 1. BrowserManager.js
```javascript
class BrowserManager {
  constructor(options = {}) {
    this.maxInstances = options.maxInstances || 3;
    this.browsers = new Map();
    this.availableBrowsers = [];
  }

  async createBrowser() {
    // 새 브라우저 인스턴스 생성
  }

  async getAvailableBrowser() {
    // 사용 가능한 브라우저 반환
  }

  async releaseBrowser(browserId) {
    // 브라우저 해제
  }

  async closeAll() {
    // 모든 브라우저 종료
  }
}
```

### 2. PageController.js
```javascript
class PageController {
  constructor(page) {
    this.page = page;
  }

  async navigateToSite() {
    // 대법원 사이트 접속
  }

  async fillCaseInfo(caseData) {
    // 사건 정보 입력
  }

  async handleCaptcha() {
    // 캡차 처리
  }

  async extractProgressData() {
    // 진행내용 추출
  }
}
```

### 3. 병렬 처리 로직
```javascript
class ParallelProcessor {
  constructor(browserManager, caseData) {
    this.browserManager = browserManager;
    this.caseData = caseData;
  }

  async processAllCases() {
    const promises = this.caseData.map(caseItem => 
      this.processSingleCase(caseItem)
    );
    
    return Promise.allSettled(promises);
  }

  async processSingleCase(caseItem) {
    const browser = await this.browserManager.getAvailableBrowser();
    // 사건 처리 로직
  }
}
```

## 📊 성능 비교 예상

| 항목 | Cypress | Puppeteer |
|------|---------|-----------|
| 메모리 사용량 | 높음 (단일 브라우저) | 낮음 (분산 처리) |
| 처리 속도 | 중간 | 빠름 |
| 병렬 처리 | 제한적 | 완전 지원 |
| 디버깅 | 우수 | 보통 |
| 개발 복잡도 | 낮음 | 높음 |

## 🚀 마이그레이션 단계

1. **1단계**: 기본 Puppeteer 설정 및 단일 사건 처리
2. **2단계**: 다중 브라우저 병렬 처리 구현
3. **3단계**: 캡차 처리 및 Python 연동
4. **4단계**: 진행내용 추출 기능 구현
5. **5단계**: 성능 최적화 및 테스트

## ⚠️ 주의사항

- Python GUI 연동 방식 재검토 필요
- 기존 Cypress 테스트 케이스와 100% 호환성 보장
- 메모리 누수 방지를 위한 브라우저 인스턴스 관리
- 에러 처리 및 복구 로직 강화


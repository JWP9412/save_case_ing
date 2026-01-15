/**
 * Puppeteer 자동화 메인 실행 파일
 * 다중 브라우저를 이용한 병렬 사건 처리
 */

const BrowserManager = require('./BrowserManager');
const ParallelProcessor = require('./ParallelProcessor');
const fs = require('fs').promises;
const path = require('path');

class PuppeteerAutomation {
  constructor() {
    this.browserManager = null;
    this.caseData = [];
  }

  /**
   * 초기화
   */
  async initialize() {
    try {
      console.log('🚀 Puppeteer 자동화 시스템 초기화 중...');

      // 브라우저 매니저 초기화
      this.browserManager = new BrowserManager({
        maxInstances: 3, // 최대 3개 브라우저 인스턴스
        headless: true, // 백그라운드에서 실행 (Python GUI 사용)
        browserOptions: {
          devtools: false, // 개발자 도구 닫기 (속도 향상)
          slowMo: 0 // 지연 없음 (최고 속도)
        }
      });

      await this.browserManager.initialize();

      // 사건 데이터 로드
      await this.loadCaseData();

      console.log('✅ 초기화 완료');
      return true;
    } catch (error) {
      console.error('❌ 초기화 실패:', error);
      throw error;
    }
  }

  /**
   * 사건 데이터 로드
   */
  async loadCaseData() {
    try {
      const fixturesPath = path.join(__dirname, '..', 'cypress', 'fixtures', 'cases_chunk_0.json');
      const data = await fs.readFile(fixturesPath, 'utf8');
      this.caseData = JSON.parse(data);

      console.log(`📋 사건 데이터 로드 완료: ${this.caseData.length}개 사건`);
      return this.caseData;
    } catch (error) {
      console.error('❌ 사건 데이터 로드 실패:', error);
      throw error;
    }
  }

  /**
   * 단일 사건 처리 (테스트용)
   */
  async processSingleCase(caseIndex = 0) {
    if (caseIndex >= this.caseData.length) {
      throw new Error(`사건 인덱스가 범위를 벗어났습니다: ${caseIndex}`);
    }

    const singleCase = [this.caseData[caseIndex]];
    const processor = new ParallelProcessor(this.browserManager, singleCase);

    console.log(`🔄 단일 사건 처리 시작: ${singleCase[0][2]}-${singleCase[0][3]}`);

    const result = await processor.processAllCases();
    return result;
  }

  /**
   * 대화형 캡차 처리용 단일 사건 처리
   */
  async processSingleCaseWithCaptcha(caseNumber, defendant, court, captchaInput, browserWsUrl = null) {
    try {
      console.log(`🔄 캡차 입력 처리 시작: ${caseNumber}`);

      let browserInfo, browserId, page, reconnectedBrowser;

      // WebSocket URL이 제공된 경우 기존 브라우저에 재연결
      if (browserWsUrl) {
        try {
          console.log(`🔗 [STEP 0.1] 기존 브라우저에 재연결 시도: ${browserWsUrl.substring(0, 50)}...`);
          const puppeteer = require('puppeteer');
          console.log(`🔗 [STEP 0.2] puppeteer.connect() 호출 중...`);
          reconnectedBrowser = await puppeteer.connect({ browserWSEndpoint: browserWsUrl });
          console.log(`✅ [STEP 0.3] puppeteer.connect() 성공`);

          const pages = await reconnectedBrowser.pages();
          console.log(`📄 [STEP 0.4] 총 페이지 수: ${pages.length}`);

          // 모든 페이지 URL 출력
          for (let i = 0; i < pages.length; i++) {
            console.log(`📄 [STEP 0.5] 페이지 ${i}: ${pages[i].url()}`);
          }

          // 대법원 사이트가 열려있는 페이지 찾기 (about:blank 제외)
          page = pages.find(p => p.url().includes('ssgo.scourt.go.kr'));

          if (!page) {
            console.log(`⚠️ [STEP 0.6] 대법원 페이지 없음, about:blank 아닌 페이지 찾기...`);
            // 대법원 페이지를 못 찾으면 about:blank가 아닌 첫 번째 페이지 사용
            page = pages.find(p => p.url() !== 'about:blank');

            if (!page) {
              // 그래도 없으면 첫 번째 페이지 사용
              console.log(`⚠️ [STEP 0.7] 유효한 페이지 없음, pages[0] 사용`);
              page = pages[0];
              console.log(`⚠️ 대법원 페이지를 찾을 수 없습니다. 첫 번째 페이지 사용: ${page.url()}`);
            } else {
              console.log(`⚠️ 대법원 페이지를 찾을 수 없습니다. about:blank가 아닌 페이지 사용: ${page.url()}`);
            }
          } else {
            console.log(`✅ 대법원 페이지 찾음: ${page.url()}`);
          }

          browserId = 'reconnected_browser';
          console.log(`✅ [STEP 0.8] 브라우저 재연결 성공!`);
        } catch (error) {
          console.error(`❌ [STEP 0.ERROR] 브라우저 재연결 실패: ${error.message}`);
          console.error(`❌ [STEP 0.ERROR] 에러 스택: ${error.stack}`);
          throw error;
        }
      } else {
        // 새 브라우저 시작 (기존 방식)
        browserInfo = await this.browserManager.getBrowser();
        browserId = browserInfo.id;
        page = browserInfo.page;
      }

      const PageController = require('./PageController');
      const pageController = new PageController(page, browserId);

      // 재연결 시에는 이미 페이지가 로드되어 있으므로 캡차 입력만 진행
      if (!browserWsUrl) {
        // 새 브라우저인 경우에만 페이지 로드 및 입력
        await pageController.navigateToSite();
        await pageController.selectCourt(court);
        await pageController.checkCaseNumberInputMode();
        await pageController.checkSaveSearchResult();
        await pageController.inputCaseNumber(caseNumber);
        await pageController.inputPartyName(defendant);
      } else {
        // 재연결인 경우 이미 입력되어 있으므로 스킵
        console.log(`⏩ 재연결된 브라우저 - 페이지 로드 스킵 (캡차 유지!)`);

        // [디버깅] 재연결 후 페이지 상태 확인
        const currentUrl = page.url();
        console.log(`📄 [DEBUG] 현재 페이지 URL: ${currentUrl}`);
        const pageTitle = await page.title();
        console.log(`📄 [DEBUG] 페이지 제목: ${pageTitle}`);

        // about:blank 또는 빈 페이지 체크
        if (currentUrl === 'about:blank' || !currentUrl.includes('ssgo.scourt.go.kr')) {
          console.log(`❌ [ERROR] 페이지가 닫혔거나 변경되었습니다! URL: ${currentUrl}`);
          // 디버그용 스크린샷
          const screenshotPath = `screenshots/debug_${caseNumber}_${Date.now()}.png`;
          await page.screenshot({ path: screenshotPath });
          console.log(`📸 [DEBUG] 디버그 스크린샷 저장: ${screenshotPath}`);
          throw new Error(`브라우저 페이지가 닫혔습니다. 현재 URL: ${currentUrl}`);
        }

        // 캡차 입력 필드 존재 여부 확인
        const captchaField = await page.$('#mf_ssgoTopMainTab_contents_content1_body_ibx_answer');
        if (!captchaField) {
          console.log(`❌ [DEBUG] 캡차 입력 필드 없음! 페이지 상태가 변경되었습니다!`);
          // 디버그용 스크린샷
          const screenshotPath = `screenshots/debug_${caseNumber}_${Date.now()}.png`;
          await page.screenshot({ path: screenshotPath });
          console.log(`📸 [DEBUG] 디버그 스크린샷 저장: ${screenshotPath}`);
          throw new Error('캡차 입력 필드를 찾을 수 없습니다. 페이지 상태를 확인하세요.');
        } else {
          console.log(`✅ [DEBUG] 캡차 입력 필드 확인됨!`);
        }
      }

      // 캡차 입력 (이미 입력된 값 사용)
      console.log(`🔐 [STEP 1] 캡차 입력 시작: ${captchaInput}`);
      await pageController.inputCaptcha(captchaInput);
      console.log(`✅ [STEP 1] 캡차 입력 완료`);

      console.log(`🔍 [STEP 2] 검색 실행 시작`);
      await pageController.performSearch();
      console.log(`✅ [STEP 2] 검색 실행 완료`);

      console.log(`📊 [STEP 3] 진행내용 데이터 추출 시작`);
      const progressData = await pageController.extractProgressData(caseNumber);
      console.log(`✅ [STEP 3] 진행내용 데이터 추출 완료: ${progressData.length}개 행`);

      const result = {
        caseNumber,
        defendant,
        court,
        captchaInput,
        progressData,
        success: true,
        timestamp: new Date().toISOString()
      };

      // 결과 저장
      const resultsDir = path.join(process.cwd(), 'results');
      await fs.mkdir(resultsDir, { recursive: true });
      const filename = `case_result_${caseNumber}_${Date.now()}.json`;
      const filepath = path.join(resultsDir, filename);
      await fs.writeFile(filepath, JSON.stringify(result, null, 2));

      console.log(`✅ 처리 완료: ${caseNumber}`);
      console.log(`📊 진행내용 데이터: ${progressData.length}개 행 추출 성공`);

      // WebSocket으로 재연결한 브라우저 닫기
      if (browserWsUrl) {
        console.log(`🔌 WebSocket 재연결 브라우저 닫는 중...`);
        try {
          await reconnectedBrowser.close();
          console.log(`✅ 브라우저 닫기 완료`);
        } catch (error) {
          console.error(`⚠️ 브라우저 닫기 실패: ${error.message}`);
        }
      } else {
        await this.browserManager.releaseBrowser(browserId);
      }

      return result;
    } catch (error) {
      console.error(`❌ 처리 실패: ${caseNumber} - ${error.message}`);
      throw error;
    }
  }

  async processSingleCaseWithInteractiveCaptcha(caseNumber, defendant, court) {
    try {
      console.log(`🔄 대화형 캡차 처리 시작: ${caseNumber}`);

      // 브라우저 인스턴스 가져오기
      const browserInfo = await this.browserManager.getBrowser();
      const browserId = browserInfo.id;
      const page = browserInfo.page;

      // PageController 인스턴스 생성
      const PageController = require('./PageController');
      const pageController = new PageController(page, browserId);

      // 사이트 접속
      await pageController.navigateToSite();

      // 법원 선택
      await pageController.selectCourt(court);

      // 사건번호 입력 모드 체크
      await pageController.checkCaseNumberInputMode();

      // 결과 저장 체크박스 체크
      await pageController.checkSaveSearchResult();

      // 사건번호 입력
      await pageController.inputCaseNumber(caseNumber);

      // 당사자명 입력
      await pageController.inputPartyName(defendant);

      // 캡차 처리 (Python GUI 자동 실행)
      const captchaInput = await pageController.handleCaptcha(caseNumber);

      // 검색 실행
      await pageController.performSearch();

      // 진행내용 데이터 추출
      const progressData = await pageController.extractProgressData();

      // 결과 저장
      const result = {
        caseNumber,
        defendant,
        court,
        captchaInput,
        progressData,
        success: true,
        timestamp: new Date().toISOString()
      };

      // JSON 파일로 저장
      const resultsDir = path.join(process.cwd(), 'results');
      await fs.mkdir(resultsDir, { recursive: true });

      const filename = `case_result_${caseNumber}_${Date.now()}.json`;
      const filepath = path.join(resultsDir, filename);
      await fs.writeFile(filepath, JSON.stringify(result, null, 2));

      console.log(`✅ 처리 완료: ${caseNumber}`);
      console.log(`📊 진행내용 데이터: ${progressData.length}개 행 추출 성공`);

      // 브라우저 반환
      await this.browserManager.releaseBrowser(browserId);

      return result;

    } catch (error) {
      console.error(`❌ 처리 실패: ${caseNumber} - ${error.message}`);
      throw error;
    }
  }

  /**
   * 모든 사건 병렬 처리
   */
  async processAllCases() {
    const processor = new ParallelProcessor(this.browserManager, this.caseData);

    console.log(`🔄 모든 사건 병렬 처리 시작: ${this.caseData.length}개 사건`);

    const result = await processor.processAllCases();

    // 최종 리포트 생성
    const report = await processor.generateReport();

    return {
      ...result,
      report
    };
  }

  /**
   * 정리 작업
   */
  async cleanup() {
    try {
      if (this.browserManager) {
        await this.browserManager.closeAll();
      }
      console.log('🧹 정리 작업 완료');
    } catch (error) {
      console.error('❌ 정리 작업 실패:', error);
    }
  }
}

// 메인 실행 함수
async function main() {
  const automation = new PuppeteerAutomation();

  try {
    // 초기화
    await automation.initialize();

    // 명령행 인수 확인
    const args = process.argv.slice(2);
    const command = args[0] || 'all';

    let result;

    switch (command) {
      case 'single':
        const caseIndex = parseInt(args[1]) || 0;
        console.log(`🎯 단일 사건 처리 모드: 인덱스 ${caseIndex}`);
        result = await automation.processSingleCase(caseIndex);
        break;

      case '--single-case':
        // 대화형 캡차 처리용 단일 사건 처리
        console.log(`📋 [DEBUG] 전체 인자:`, args);
        const caseNumber = args[1];
        const defendant = args[3]; // --defendant 다음 값
        const court = args[5]; // --court 다음 값
        const captchaInput = args[7]; // --captcha 다음 값
        const browserWsUrl = args[9]; // --browser-ws-url 다음 값 (선택적)

        console.log(`📋 [DEBUG] 파싱된 값:`);
        console.log(`  - 사건번호: ${caseNumber}`);
        console.log(`  - 피고: ${defendant}`);
        console.log(`  - 법원: ${court}`);
        console.log(`  - 캡차: ${captchaInput}`);
        console.log(`  - WS URL: ${browserWsUrl ? browserWsUrl.substring(0, 50) + '...' : 'undefined'}`);

        if (!caseNumber || !defendant || !court) {
          throw new Error('사건번호, 피고, 법원 정보가 필요합니다.');
        }

        if (captchaInput) {
          console.log(`🎯 캡차 입력 처리 모드: ${caseNumber} (캡차: ${captchaInput})`);
          if (browserWsUrl) {
            console.log(`🔗 브라우저 재연결 모드: ${browserWsUrl}`);
          }
          result = await automation.processSingleCaseWithCaptcha(caseNumber, defendant, court, captchaInput, browserWsUrl);
        } else {
          console.log(`🎯 대화형 캡차 처리 모드: ${caseNumber}`);
          result = await automation.processSingleCaseWithInteractiveCaptcha(caseNumber, defendant, court);
        }
        break;

      case 'all':
      default:
        console.log(`🎯 전체 사건 병렬 처리 모드`);
        result = await automation.processAllCases();
        break;
    }

    // 결과 출력
    console.log('\n📊 처리 결과:');
    if (result) {
      console.log(`- 총 사건 수: ${result.totalCases || 1}`);
      console.log(`- 성공: ${result.success?.length || (result.success ? 1 : 0)}개`);
      console.log(`- 실패: ${result.errors?.length || (result.success === false ? 1 : 0)}개`);
      console.log(`- 처리 시간: ${result.duration?.toFixed(2) || 'N/A'}초`);

      if (result.errors && result.errors.length > 0) {
        console.log('\n❌ 실패한 사건들:');
        result.errors.forEach((error, index) => {
          console.log(`${index + 1}. ${error.caseData?.[2]}-${error.caseData?.[3]}: ${error.reason}`);
        });
      }
    } else {
      console.log('- 결과 없음');
    }

  } catch (error) {
    console.error('❌ 실행 중 오류 발생:', error);
    process.exit(1);
  } finally {
    // 정리 작업
    await automation.cleanup();
  }
}

// 스크립트가 직접 실행된 경우에만 main 함수 호출
if (require.main === module) {
  main().catch(console.error);
}

module.exports = PuppeteerAutomation;

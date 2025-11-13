/**
 * 브라우저 인스턴스 관리자
 * 다중 브라우저 창을 효율적으로 관리하고 병렬 처리를 지원합니다.
 */

const puppeteer = require('puppeteer');
const pLimit = require('p-limit').default || require('p-limit');

class BrowserManager {
  constructor(options = {}) {
    this.maxInstances = options.maxInstances || 3;
    this.browsers = new Map();
    this.availableBrowsers = [];
    this.busyBrowsers = new Set();
    this.limit = pLimit(this.maxInstances);
    this.browserOptions = {
      headless: options.headless !== false, // 기본값: headless
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-accelerated-2d-canvas',
        '--no-first-run',
        '--no-zygote',
        '--disable-gpu',
        '--window-size=1920,1080'
      ],
      ...options.browserOptions
    };
  }

  /**
   * 브라우저 인스턴스 생성
   */
  async createBrowser() {
    try {
      const browser = await puppeteer.launch(this.browserOptions);
      const browserId = `browser_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      
      this.browsers.set(browserId, {
        browser,
        createdAt: new Date(),
        isBusy: false
      });
      
      this.availableBrowsers.push(browserId);
      
      console.log(`✅ 브라우저 인스턴스 생성됨: ${browserId}`);
      return browserId;
    } catch (error) {
      console.error('❌ 브라우저 생성 실패:', error);
      throw error;
    }
  }

  /**
   * 사용 가능한 브라우저 반환
   */
  async getAvailableBrowser() {
    return this.limit(async () => {
      // 사용 가능한 브라우저가 없으면 새로 생성
      if (this.availableBrowsers.length === 0) {
        await this.createBrowser();
      }

      const browserId = this.availableBrowsers.shift();
      if (!browserId || !this.browsers.has(browserId)) {
        throw new Error('사용 가능한 브라우저가 없습니다');
      }

      const browserInfo = this.browsers.get(browserId);
      browserInfo.isBusy = true;
      this.busyBrowsers.add(browserId);

      console.log(`🔄 브라우저 사용 중: ${browserId}`);
      return {
        id: browserId,
        browser: browserInfo.browser,
        page: await browserInfo.browser.newPage()
      };
    });
  }

  /**
   * 브라우저 가져오기 (간단한 버전)
   */
  async getBrowser() {
    return this.getAvailableBrowser();
  }

  /**
   * 페이지 가져오기
   */
  async getPage(browserId) {
    if (!this.browsers.has(browserId)) {
      throw new Error(`브라우저를 찾을 수 없습니다: ${browserId}`);
    }

    const browserInfo = this.browsers.get(browserId);
    return await browserInfo.browser.newPage();
  }

  /**
   * 브라우저 해제
   */
  async releaseBrowser(browserId) {
    if (!this.browsers.has(browserId)) {
      console.warn(`⚠️ 브라우저를 찾을 수 없습니다: ${browserId}`);
      return;
    }

    const browserInfo = this.browsers.get(browserId);
    browserInfo.isBusy = false;
    this.busyBrowsers.delete(browserId);
    this.availableBrowsers.push(browserId);

    console.log(`🔄 브라우저 해제됨: ${browserId}`);
  }

  /**
   * 브라우저 완전 종료
   */
  async closeBrowser(browserId) {
    if (!this.browsers.has(browserId)) {
      return;
    }

    const browserInfo = this.browsers.get(browserId);
    await browserInfo.browser.close();
    this.browsers.delete(browserId);
    this.availableBrowsers = this.availableBrowsers.filter(id => id !== browserId);
    this.busyBrowsers.delete(browserId);

    console.log(`❌ 브라우저 종료됨: ${browserId}`);
  }

  /**
   * 모든 브라우저 종료
   */
  async closeAll() {
    console.log('🔄 모든 브라우저 종료 중...');
    
    const closePromises = Array.from(this.browsers.keys()).map(browserId => 
      this.closeBrowser(browserId)
    );
    
    await Promise.all(closePromises);
    console.log('✅ 모든 브라우저가 종료되었습니다');
  }

  /**
   * 브라우저 상태 정보
   */
  getStatus() {
    return {
      total: this.browsers.size,
      available: this.availableBrowsers.length,
      busy: this.busyBrowsers.size,
      maxInstances: this.maxInstances
    };
  }

  /**
   * 초기화 - 최대 인스턴스 수만큼 브라우저 생성
   */
  async initialize() {
    console.log(`🚀 브라우저 매니저 초기화 중... (최대 ${this.maxInstances}개 인스턴스)`);
    
    const initPromises = Array.from({ length: this.maxInstances }, () => 
      this.createBrowser()
    );
    
    await Promise.all(initPromises);
    console.log(`✅ 브라우저 매니저 초기화 완료: ${this.getStatus().total}개 인스턴스`);
  }
}

module.exports = BrowserManager;

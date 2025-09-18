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
        headless: false, // 디버깅을 위해 브라우저 창 표시
        browserOptions: {
          devtools: true, // 개발자 도구 열기
          slowMo: 500 // 각 동작 사이 500ms 지연 (디버깅용)
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
        
      case 'all':
      default:
        console.log(`🎯 전체 사건 병렬 처리 모드`);
        result = await automation.processAllCases();
        break;
    }
    
    // 결과 출력
    console.log('\n📊 처리 결과:');
    console.log(`- 총 사건 수: ${result.totalCases}`);
    console.log(`- 성공: ${result.success.length}개`);
    console.log(`- 실패: ${result.errors.length}개`);
    console.log(`- 처리 시간: ${result.duration?.toFixed(2)}초`);
    
    if (result.errors.length > 0) {
      console.log('\n❌ 실패한 사건들:');
      result.errors.forEach((error, index) => {
        console.log(`${index + 1}. ${error.caseData?.[2]}-${error.caseData?.[3]}: ${error.reason}`);
      });
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

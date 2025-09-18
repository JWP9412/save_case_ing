/**
 * 병렬 처리 프로세서
 * 다중 브라우저를 이용한 사건 병렬 처리를 담당합니다.
 */

const fs = require('fs').promises;
const path = require('path');
const PageController = require('./PageController');

class ParallelProcessor {
  constructor(browserManager, caseData) {
    this.browserManager = browserManager;
    this.caseData = caseData;
    this.results = [];
    this.errors = [];
  }

  /**
   * 모든 사건 병렬 처리
   */
  async processAllCases() {
    console.log(`🚀 병렬 처리 시작: ${this.caseData.length}개 사건`);
    console.log(`📊 브라우저 상태:`, this.browserManager.getStatus());
    
    const startTime = Date.now();
    
    try {
      // 각 사건을 병렬로 처리
      const promises = this.caseData.map((caseItem, index) => 
        this.processSingleCase(caseItem, index)
      );
      
      // 모든 사건 처리 완료 대기
      const results = await Promise.allSettled(promises);
      
      const endTime = Date.now();
      const duration = (endTime - startTime) / 1000;
      
      // 결과 분석
      this.analyzeResults(results);
      
      console.log(`✅ 병렬 처리 완료: ${duration.toFixed(2)}초`);
      console.log(`📊 성공: ${this.results.length}개, 실패: ${this.errors.length}개`);
      
      return {
        success: this.results,
        errors: this.errors,
        duration,
        totalCases: this.caseData.length
      };
    } catch (error) {
      console.error('❌ 병렬 처리 중 오류 발생:', error);
      throw error;
    } finally {
      // 모든 브라우저 정리
      await this.browserManager.closeAll();
    }
  }

  /**
   * 단일 사건 처리
   */
  async processSingleCase(caseItem, index) {
    const [id, courtName, caseNumber, partyName, status] = caseItem;
    const caseId = `${caseNumber}-${partyName}`;
    
    console.log(`\n🔄 사건 처리 시작 (${index + 1}/${this.caseData.length}): ${caseId}`);
    
    let browserInstance = null;
    let pageController = null;
    
    try {
      // 브라우저 인스턴스 가져오기
      browserInstance = await this.browserManager.getAvailableBrowser();
      pageController = new PageController(browserInstance.page, browserInstance.id);
      
      // 사건 처리 단계별 실행
      const result = await this.executeCaseSteps(pageController, caseItem);
      
      console.log(`✅ 사건 처리 완료: ${caseId}`);
      return result;
      
    } catch (error) {
      console.error(`❌ 사건 처리 실패: ${caseId}`, error.message);
      return {
        success: false,
        caseId,
        error: error.message,
        caseData: caseItem
      };
    } finally {
      // 브라우저 인스턴스 해제
      if (browserInstance) {
        await this.browserManager.releaseBrowser(browserInstance.id);
      }
    }
  }

  /**
   * 사건 처리 단계별 실행
   */
  async executeCaseSteps(pageController, caseData) {
    const [id, courtName, caseNumber, partyName, status] = caseData;
    const caseId = `${caseNumber}-${partyName}`;
    
    try {
      // 1. 사이트 접속
      await pageController.navigateToSite();
      
      // 2. 사건번호입력모드 체크
      await pageController.checkCaseNumberInputMode();
      
      // 3. 법원 선택
      await pageController.selectCourt(courtName);
      
      // 4. 사건번호 입력
      await pageController.inputCaseNumber(caseNumber);
      
      // 5. 당사자명 입력
      await pageController.inputPartyName(partyName);
      
      // 6. 캡차 처리
      const captchaInput = await pageController.handleCaptcha(caseNumber);
      
      // 7. 검색 실행
      await pageController.performSearch();
      
      // 8. 진행내용 데이터 추출
      const progressData = await pageController.extractProgressData(caseNumber);
      
      // 9. 최종 스크린샷
      await pageController.takeScreenshot(caseNumber, 'final');
      
      // 10. 결과 저장
      const result = {
        success: true,
        caseId,
        caseData: {
          id: id,
          courtName: courtName,
          caseNumber: caseNumber,
          partyName: partyName,
          status: status
        },
        captchaInput,
        progressData,
        extractedAt: new Date().toISOString(),
        browserId: pageController.browserId
      };
      
      // JSON 파일로 결과 저장
      await this.saveCaseResult(result);
      
      return result;
      
    } catch (error) {
      // 에러 발생 시에도 스크린샷 촬영
      try {
        await pageController.takeScreenshot(caseNumber, 'error');
      } catch (screenshotError) {
        console.error('스크린샷 촬영 실패:', screenshotError.message);
      }
      
      throw error;
    }
  }

  /**
   * 사건 결과 저장
   */
  async saveCaseResult(result) {
    try {
      const filename = `case_result_${result.caseId.replace(/[^a-zA-Z0-9가-힣]/g, '_')}.json`;
      const filepath = path.join(__dirname, '..', 'results', filename);
      
      // results 디렉토리 생성
      await fs.mkdir(path.dirname(filepath), { recursive: true });
      
      // JSON 파일로 저장
      await fs.writeFile(filepath, JSON.stringify(result, null, 2), 'utf8');
      
      console.log(`💾 사건 결과 저장: ${filename}`);
    } catch (error) {
      console.error('❌ 사건 결과 저장 실패:', error.message);
    }
  }

  /**
   * 결과 분석
   */
  analyzeResults(results) {
    this.results = [];
    this.errors = [];
    
    results.forEach((result, index) => {
      if (result.status === 'fulfilled' && result.value.success) {
        this.results.push(result.value);
      } else {
        const error = {
          index,
          status: result.status,
          reason: result.reason || result.value?.error || '알 수 없는 오류',
          caseData: result.value?.caseData || this.caseData[index]
        };
        this.errors.push(error);
      }
    });
  }

  /**
   * 최종 결과 리포트 생성
   */
  async generateReport() {
    const report = {
      timestamp: new Date().toISOString(),
      totalCases: this.caseData.length,
      successCount: this.results.length,
      errorCount: this.errors.length,
      successRate: (this.results.length / this.caseData.length * 100).toFixed(2) + '%',
      results: this.results,
      errors: this.errors
    };
    
    const reportPath = path.join(__dirname, '..', 'results', 'processing_report.json');
    await fs.writeFile(reportPath, JSON.stringify(report, null, 2), 'utf8');
    
    console.log(`📊 처리 리포트 생성: ${reportPath}`);
    return report;
  }
}

module.exports = ParallelProcessor;

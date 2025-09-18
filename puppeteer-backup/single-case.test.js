/**
 * 단일 사건 처리 테스트
 * Puppeteer 자동화의 기본 기능을 테스트합니다.
 */

const PuppeteerAutomation = require('../src/index');

async function testSingleCase() {
  console.log('🧪 단일 사건 처리 테스트 시작');
  
  const automation = new PuppeteerAutomation();
  
  try {
    // 초기화
    await automation.initialize();
    
    // 첫 번째 사건 처리 (인덱스 0)
    const result = await automation.processSingleCase(0);
    
    console.log('\n📊 테스트 결과:');
    console.log(`- 성공: ${result.success.length}개`);
    console.log(`- 실패: ${result.errors.length}개`);
    console.log(`- 처리 시간: ${result.duration?.toFixed(2)}초`);
    
    if (result.success.length > 0) {
      const successCase = result.success[0];
      console.log('\n✅ 성공한 사건 정보:');
      console.log(`- 사건번호: ${successCase.caseData[2]}`);
      console.log(`- 당사자명: ${successCase.caseData[3]}`);
      console.log(`- 캡차 입력: ${successCase.captchaInput}`);
      console.log(`- 진행내용 행 수: ${successCase.progressData?.length || 0}`);
    }
    
    if (result.errors.length > 0) {
      console.log('\n❌ 실패한 사건 정보:');
      result.errors.forEach((error, index) => {
        console.log(`${index + 1}. ${error.caseData?.[2]}-${error.caseData?.[3]}: ${error.reason}`);
      });
    }
    
    return result.success.length > 0;
    
  } catch (error) {
    console.error('❌ 테스트 실패:', error);
    return false;
  } finally {
    await automation.cleanup();
  }
}

// 테스트 실행
if (require.main === module) {
  testSingleCase()
    .then(success => {
      if (success) {
        console.log('\n🎉 테스트 성공!');
        process.exit(0);
      } else {
        console.log('\n💥 테스트 실패!');
        process.exit(1);
      }
    })
    .catch(error => {
      console.error('💥 테스트 실행 중 오류:', error);
      process.exit(1);
    });
}

module.exports = testSingleCase;

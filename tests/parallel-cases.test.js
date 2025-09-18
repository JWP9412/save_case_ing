/**
 * 병렬 사건 처리 테스트
 * 다중 브라우저를 이용한 병렬 처리를 테스트합니다.
 */

const PuppeteerAutomation = require('../src/index');

async function testParallelCases() {
  console.log('🧪 병렬 사건 처리 테스트 시작');
  
  const automation = new PuppeteerAutomation();
  
  try {
    // 초기화
    await automation.initialize();
    
    // 모든 사건 병렬 처리
    const result = await automation.processAllCases();
    
    console.log('\n📊 병렬 처리 결과:');
    console.log(`- 총 사건 수: ${result.totalCases}`);
    console.log(`- 성공: ${result.success.length}개`);
    console.log(`- 실패: ${result.errors.length}개`);
    console.log(`- 처리 시간: ${result.duration?.toFixed(2)}초`);
    console.log(`- 평균 처리 시간: ${(result.duration / result.totalCases).toFixed(2)}초/사건`);
    
    // 성공률 계산
    const successRate = (result.success.length / result.totalCases * 100).toFixed(2);
    console.log(`- 성공률: ${successRate}%`);
    
    if (result.success.length > 0) {
      console.log('\n✅ 성공한 사건들:');
      result.success.forEach((successCase, index) => {
        console.log(`${index + 1}. ${successCase.caseData[2]}-${successCase.caseData[3]} (${successCase.progressData?.length || 0}개 진행내용)`);
      });
    }
    
    if (result.errors.length > 0) {
      console.log('\n❌ 실패한 사건들:');
      result.errors.forEach((error, index) => {
        console.log(`${index + 1}. ${error.caseData?.[2]}-${error.caseData?.[3]}: ${error.reason}`);
      });
    }
    
    // 성공률이 80% 이상이면 테스트 통과
    const testPassed = parseFloat(successRate) >= 80;
    
    if (testPassed) {
      console.log('\n🎉 병렬 처리 테스트 성공!');
    } else {
      console.log('\n💥 병렬 처리 테스트 실패! (성공률 80% 미만)');
    }
    
    return testPassed;
    
  } catch (error) {
    console.error('❌ 테스트 실패:', error);
    return false;
  } finally {
    await automation.cleanup();
  }
}

// 테스트 실행
if (require.main === module) {
  testParallelCases()
    .then(success => {
      if (success) {
        console.log('\n🎉 모든 테스트 통과!');
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

module.exports = testParallelCases;


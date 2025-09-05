describe('단순한 접근 방식 테스트', function () {
  it('사건번호입력모드 체크 → 사건번호 입력 → 당사자명 입력', function() {
    // 구글시트 데이터 가져오기
    const cases = require('../fixtures/cases_chunk_0.json');
    const [rowIndex, court, caseNumber, manager] = cases[0];
    
    cy.log(`🔍 처리할 사건: ${court} ${caseNumber} (${manager})`);
    
    // 사이트 접속
    cy.visit('https://www.scourt.go.kr/portal/information/events/search/search.jsp');
    cy.wait(15000); // 충분한 로딩 대기
    cy.log('✅ 사이트 접속 완료');
    
    // 1단계: 사건번호입력모드 체크박스 체크
    cy.log('🎯 1단계: 사건번호입력모드 체크박스 찾기');
    
    // 여러 가능한 체크박스 선택자들
    const checkboxSelectors = [
      'input[type="checkbox"]',
      'input[name*="mode"]',
      'input[name*="input"]',
      'input[id*="mode"]',
      'input[id*="input"]'
    ];
    
    let checkboxFound = false;
    
    checkboxSelectors.forEach(selector => {
      cy.get('body').then($body => {
        const checkboxes = $body.find(selector);
        if (checkboxes.length > 0 && !checkboxFound) {
          cy.log(`📋 체크박스 발견: ${selector} (${checkboxes.length}개)`);
          
          checkboxes.each((index, checkbox) => {
            const id = checkbox.id || '없음';
            const name = checkbox.name || '없음';
            const title = checkbox.title || '없음';
            cy.log(`  체크박스 ${index}: id="${id}", name="${name}", title="${title}"`);
          });
          
          // 첫 번째 체크박스 체크
          cy.get(selector).first().check({ force: true });
          cy.log('✅ 사건번호입력모드 체크박스 체크 완료');
          checkboxFound = true;
        }
      });
    });
    
    cy.wait(1000);
    
    // 2단계: 사건번호 입력
    cy.log('🎯 2단계: 사건번호 입력');
    
    // 사건번호에서 숫자만 추출 (예: "2024가합51101" → "51101")
    const serialNumber = caseNumber.match(/[0-9]+$/)[0]; // 마지막 숫자 그룹
    cy.log(`📝 입력할 사건번호: ${serialNumber}`);
    
    // 여러 가능한 사건번호 입력 필드들
    const serialInputSelectors = [
      'input[type="text"]',
      'input[maxlength="7"]',
      'input[maxlength="6"]',
      'input[name*="serial"]',
      'input[id*="serial"]',
      'input[name*="사건"]',
      'input[id*="사건"]'
    ];
    
    let serialInputFound = false;
    
    serialInputSelectors.forEach(selector => {
      cy.get('body').then($body => {
        const inputs = $body.find(selector);
        if (inputs.length > 0 && !serialInputFound) {
          cy.log(`📝 사건번호 입력 필드 후보: ${selector} (${inputs.length}개)`);
          
          inputs.each((index, input) => {
            const id = input.id || '없음';
            const name = input.name || '없음';
            const maxLength = input.maxLength || '없음';
            const placeholder = input.placeholder || '없음';
            cy.log(`  입력 필드 ${index}: id="${id}", name="${name}", maxLength=${maxLength}, placeholder="${placeholder}"`);
          });
          
          // 첫 번째 적절한 입력 필드에 사건번호 입력
          cy.get(selector).first().then($input => {
            cy.wrap($input).clear({ force: true });
            cy.wrap($input).type(serialNumber, { force: true });
            cy.log(`✅ 사건번호 입력 완료: ${serialNumber}`);
            serialInputFound = true;
          });
        }
      });
    });
    
    cy.wait(1000);
    
    // 3단계: 당사자명 입력
    cy.log('🎯 3단계: 당사자명 입력');
    cy.log(`👤 입력할 당사자명: ${manager}`);
    
    // 당사자명 입력 필드 (보통 길이가 긴 텍스트 입력)
    const nameInputSelectors = [
      'input[maxlength="40"]',
      'input[maxlength="30"]',
      'input[maxlength="20"]',
      'input[name*="name"]',
      'input[name*="nm"]',
      'input[id*="name"]',
      'input[id*="nm"]',
      'input[name*="당사자"]',
      'input[id*="당사자"]'
    ];
    
    let nameInputFound = false;
    
    nameInputSelectors.forEach(selector => {
      cy.get('body').then($body => {
        const inputs = $body.find(selector);
        if (inputs.length > 0 && !nameInputFound) {
          cy.log(`👤 당사자명 입력 필드 후보: ${selector} (${inputs.length}개)`);
          
          inputs.each((index, input) => {
            const id = input.id || '없음';
            const name = input.name || '없음';
            const maxLength = input.maxLength || '없음';
            const placeholder = input.placeholder || '없음';
            cy.log(`  입력 필드 ${index}: id="${id}", name="${name}", maxLength=${maxLength}, placeholder="${placeholder}"`);
          });
          
          // 첫 번째 적절한 입력 필드에 당사자명 입력
          cy.get(selector).first().then($input => {
            cy.wrap($input).clear({ force: true });
            cy.wrap($input).type(manager, { force: true });
            cy.log(`✅ 당사자명 입력 완료: ${manager}`);
            nameInputFound = true;
          });
        }
      });
    });
    
    cy.wait(2000);
    
    // 최종 스크린샷
    cy.screenshot('simple-approach-result');
    cy.log('🎯 단순한 접근 방식 테스트 완료');
    
    // 입력 결과 확인
    cy.log('📋 입력 결과 요약:');
    cy.log(`  - 체크박스: ${checkboxFound ? '✅' : '❌'}`);
    cy.log(`  - 사건번호(${serialNumber}): ${serialInputFound ? '✅' : '❌'}`);
    cy.log(`  - 당사자명(${manager}): ${nameInputFound ? '✅' : '❌'}`);
  });
});



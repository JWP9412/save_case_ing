const cases = require('../fixtures/cases_chunk_0.json');

describe('한글 입력 문제 해결', function () {
  const [rowIndex, court, caseNumber, manager] = cases[0];
  
  it('한글이 포함된 사건번호 입력 문제 해결', function() {
    cy.log(`🔍 입력할 사건번호: "${caseNumber}"`);
    
    // 간편 사이트 접속
    cy.visit('https://ssgo.scourt.go.kr/ssgo/index.on?cortId=www');
    cy.wait(15000);
    cy.log('✅ 사이트 접속 완료');
    
    // 체크박스 체크
    cy.get('#mf_ssgoTopMainTab_contents_content1_body_cbx_chkSanoInputMode_input_0').check({ force: true });
    cy.wait(2000);
    
    // 방법 1: 천천히 한 글자씩 입력
    cy.log('🎯 방법 1: 천천히 한 글자씩 입력');
    cy.get('input[type="text"]:visible').first().then($input => {
      cy.wrap($input).clear({ force: true });
      
      // 한 글자씩 천천히 입력
      const chars = caseNumber.split('');
      chars.forEach((char, index) => {
        cy.wrap($input).type(char, { force: true, delay: 100 });
        cy.log(`글자 ${index + 1}: "${char}" 입력`);
      });
      
      cy.wait(1000);
      cy.wrap($input).then($updated => {
        cy.log(`방법 1 결과: "${$updated.val()}"`);
      });
    });
    
    cy.wait(2000);
    cy.screenshot('method1-korean-input');
    
    // 방법 2: JavaScript로 직접 값 설정
    cy.log('🎯 방법 2: JavaScript로 직접 값 설정');
    cy.get('input[type="text"]:visible').first().then($input => {
      const inputElement = $input[0];
      
      // JavaScript로 직접 값 설정
      cy.window().then(win => {
        inputElement.value = caseNumber;
        
        // 이벤트 발생시키기
        const inputEvent = new win.Event('input', { bubbles: true });
        const changeEvent = new win.Event('change', { bubbles: true });
        
        inputElement.dispatchEvent(inputEvent);
        inputElement.dispatchEvent(changeEvent);
        
        cy.log(`방법 2: JavaScript로 "${caseNumber}" 설정 완료`);
      });
      
      cy.wait(1000);
      cy.wrap($input).then($updated => {
        cy.log(`방법 2 결과: "${$updated.val()}"`);
      });
    });
    
    cy.wait(2000);
    cy.screenshot('method2-javascript-input');
    
    // 방법 3: 복사-붙여넣기 시뮬레이션
    cy.log('🎯 방법 3: 복사-붙여넣기 시뮬레이션');
    cy.get('input[type="text"]:visible').first().then($input => {
      cy.wrap($input).clear({ force: true });
      
      // Ctrl+V 이벤트 시뮬레이션
      cy.wrap($input).trigger('keydown', { 
        keyCode: 86, 
        ctrlKey: true, 
        force: true 
      });
      
      // 직접 값 설정 후 paste 이벤트
      cy.window().then(win => {
        const inputElement = $input[0];
        inputElement.value = caseNumber;
        
        const pasteEvent = new win.Event('paste', { bubbles: true });
        inputElement.dispatchEvent(pasteEvent);
        
        cy.log(`방법 3: 붙여넣기로 "${caseNumber}" 설정`);
      });
      
      cy.wait(1000);
      cy.wrap($input).then($updated => {
        cy.log(`방법 3 결과: "${$updated.val()}"`);
      });
    });
    
    cy.wait(2000);
    cy.screenshot('method3-paste-input');
    
    // 방법 4: 입력 후 강제 focus 및 blur
    cy.log('🎯 방법 4: focus와 blur로 입력 확정');
    cy.get('input[type="text"]:visible').first().then($input => {
      cy.wrap($input).clear({ force: true });
      cy.wrap($input).focus({ force: true });
      cy.wrap($input).type(caseNumber, { force: true, delay: 50 });
      cy.wrap($input).blur({ force: true });
      
      cy.wait(1000);
      cy.wrap($input).then($updated => {
        cy.log(`방법 4 결과: "${$updated.val()}"`);
      });
    });
    
    cy.wait(2000);
    
    // 최종 상태 확인
    cy.log('🔍 최종 입력 상태 확인');
    cy.get('input[type="text"]:visible').first().then($input => {
      const finalValue = $input.val();
      cy.log(`최종 입력값: "${finalValue}"`);
      
      if (finalValue === caseNumber) {
        cy.log('✅ 성공: 사건번호가 정확히 입력됨');
      } else {
        cy.log(`❌ 실패: 예상 "${caseNumber}", 실제 "${finalValue}"`);
      }
    });
    
    cy.screenshot('final-korean-input-result');
    cy.log('🎯 한글 입력 테스트 완료');
  });
});



const cases = require('../fixtures/cases_chunk_0.json');

describe('사건번호 입력 디버깅', function () {
  const [rowIndex, court, caseNumber, manager] = cases[0];
  
  it('사건번호 입력이 제대로 되는지 확인', function() {
    cy.log(`🔍 입력할 사건번호: "${caseNumber}"`);
    cy.log(`📝 입력할 당사자: "${manager}"`);
    
    // 간편 사이트 접속
    cy.visit('https://ssgo.scourt.go.kr/ssgo/index.on?cortId=www');
    cy.wait(15000);
    cy.log('✅ 사이트 접속 완료');
    
    // 1. 체크박스 체크
    cy.log('🎯 1단계: 사건번호입력모드 체크박스 체크');
    cy.get('#mf_ssgoTopMainTab_contents_content1_body_cbx_chkSanoInputMode_input_0').check({ force: true });
    cy.log('✅ 체크박스 체크 완료');
    cy.wait(2000);
    
    // 2. 사건번호 입력 전에 모든 입력 필드 확인
    cy.log('🔍 모든 입력 필드 상태 확인');
    cy.get('body').then($body => {
      const allInputs = $body.find('input[type="text"]');
      cy.log(`📝 총 ${allInputs.length}개의 텍스트 입력 필드 발견:`);
      
      allInputs.each((index, input) => {
        const id = input.id || '없음';
        const name = input.name || '없음';
        const maxLength = input.maxLength || '없음';
        const placeholder = input.placeholder || '없음';
        const value = input.value || '비어있음';
        const visible = input.offsetParent !== null;
        
        cy.log(`Input ${index}: id="${id}", name="${name}", maxLength=${maxLength}, placeholder="${placeholder}", value="${value}", visible=${visible}`);
      });
    });
    
    // 3. 사건번호 입력 시도 (여러 방법으로)
    cy.log('🎯 사건번호 입력 시도');
    
    // 방법 1: 정확한 ID로 입력
    cy.get('body').then($body => {
      const target1 = $body.find('#mf_ssgoTopMainTab_contents_content1_body_ibx_csSerial');
      if (target1.length > 0) {
        cy.log('방법 1: 정확한 ID로 입력 시도');
        cy.get('#mf_ssgoTopMainTab_contents_content1_body_ibx_csSerial').then($input => {
          cy.log(`입력 전 값: "${$input.val()}"`);
          cy.wrap($input).clear({ force: true });
          cy.wrap($input).type(caseNumber, { force: true });
          cy.wrap($input).should('have.value', caseNumber);
          cy.log(`✅ 방법 1 완료. 입력 후 값: "${$input.val()}"`);
        });
      } else {
        cy.log('❌ 방법 1: 정확한 ID를 찾을 수 없음');
      }
    });
    
    cy.wait(1000);
    
    // 방법 2: 첫 번째 보이는 텍스트 입력에 시도
    cy.log('방법 2: 첫 번째 보이는 텍스트 입력 필드 사용');
    cy.get('input[type="text"]:visible').first().then($input => {
      const id = $input.attr('id') || '없음';
      cy.log(`첫 번째 보이는 입력 필드: ${id}`);
      cy.log(`입력 전 값: "${$input.val()}"`);
      
      cy.wrap($input).clear({ force: true });
      cy.wrap($input).type(caseNumber, { force: true });
      
      cy.wrap($input).then($updatedInput => {
        cy.log(`✅ 방법 2 완료. 입력 후 값: "${$updatedInput.val()}"`);
      });
    });
    
    cy.wait(1000);
    
    // 4. 당사자명 입력 시도
    cy.log('🎯 당사자명 입력 시도');
    cy.get('body').then($body => {
      const nameInputs = $body.find('input[type="text"]:visible');
      if (nameInputs.length > 1) {
        cy.log('두 번째 보이는 입력 필드에 당사자명 입력');
        cy.get('input[type="text"]:visible').eq(1).then($input => {
          const id = $input.attr('id') || '없음';
          cy.log(`두 번째 입력 필드: ${id}`);
          cy.log(`입력 전 값: "${$input.val()}"`);
          
          cy.wrap($input).clear({ force: true });
          cy.wrap($input).type(manager, { force: true });
          
          cy.wrap($input).then($updatedInput => {
            cy.log(`✅ 당사자명 입력 완료. 입력 후 값: "${$updatedInput.val()}"`);
          });
        });
      }
    });
    
    cy.wait(2000);
    
    // 5. 최종 상태 확인
    cy.log('🔍 최종 입력 상태 확인');
    cy.get('body').then($body => {
      const allInputs = $body.find('input[type="text"]:visible');
      allInputs.each((index, input) => {
        const id = input.id || '없음';
        const value = input.value || '비어있음';
        cy.log(`최종 Input ${index}: id="${id}", value="${value}"`);
      });
    });
    
    // 스크린샷
    cy.screenshot('debug-case-input-result');
    cy.log('🎯 디버깅 완료');
  });
});



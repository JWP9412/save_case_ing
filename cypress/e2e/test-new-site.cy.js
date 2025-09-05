describe('새 사이트 테스트', () => {
  it('기본 접속 및 요소 찾기', () => {
    // 새 사이트 접속
    cy.visit('https://www.scourt.go.kr/portal/information/events/search/search.jsp');
    
    // 로딩 대기
    cy.wait(5000);
    
    // 페이지 제목 확인
    cy.title().should('include', '사건검색');
    cy.log('✅ 사이트 접속 성공');
    
    // 가능한 입력 필드들 찾기
    const inputSelectors = [
      'input[type="text"]',
      'input[name*="case"]',
      'input[id*="case"]',
      'input[name*="sa"]',
      'input[id*="sa"]'
    ];
    
    let foundInput = false;
    
    inputSelectors.forEach(selector => {
      cy.get('body').then($body => {
        if ($body.find(selector).length > 0 && !foundInput) {
          cy.log(`✅ 입력 필드 발견: ${selector}`);
          
          // 테스트 데이터 입력
          cy.get(selector).first().then($input => {
            cy.wrap($input).clear({ force: true });
            cy.wrap($input).type('2024가단1234', { force: true });
            cy.log('📝 테스트 사건번호 입력 완료');
            foundInput = true;
          });
        }
      });
    });
    
    cy.wait(1000);
    
    // 검색 버튼 찾기
    const buttonSelectors = [
      'button:contains("검색")',
      'button:contains("조회")',
      'input[type="submit"]',
      'input[value*="검색"]'
    ];
    
    let foundButton = false;
    
    buttonSelectors.forEach(selector => {
      cy.get('body').then($body => {
        if ($body.find(selector).length > 0 && !foundButton) {
          cy.log(`✅ 검색 버튼 발견: ${selector}`);
          cy.get(selector).first().click({ force: true });
          cy.log('🔍 검색 실행 완료');
          foundButton = true;
        }
      });
    });
    
    // 결과 대기
    cy.wait(3000);
    
    // 결과 확인
    cy.get('body').then($body => {
      const text = $body.text();
      if (text.includes('사건이 존재하지 않습니다') || 
          text.includes('검색 결과가 없습니다')) {
        cy.log('📋 사건 없음 확인됨');
      } else {
        cy.log('🎯 검색 결과 또는 다른 페이지로 이동됨');
      }
    });
    
    cy.log('✅ 기본 테스트 완료');
  });
});

describe('부분 자동화 테스트', () => {
  it('확인된 요소들로 테스트', () => {
    cy.visit('https://www.scourt.go.kr/portal/information/events/search/search.jsp');
    cy.wait(8000);
    
    cy.log('✅ 사이트 접속 완료');
    
    // 1. 법원 선택 (서울중앙지방법원으로 테스트)
    cy.get('#mf_ssgoTopMainTab_contents_content1_body_sbx_cortCd').then($select => {
      cy.log('✅ 법원 선택 드롭다운 발견');
      cy.wrap($select).select('서울중앙지방법원', { force: true });
      cy.log('📋 법원 선택 완료: 서울중앙지방법원');
    });
    
    cy.wait(1000);
    
    // 2. 사건번호입력모드 체크박스 체크
    cy.get('#mf_ssgoTopMainTab_contents_content1_body_cbx_chkSanoInputMode_input_0').then($checkbox => {
      cy.log('✅ 사건번호입력모드 체크박스 발견');
      cy.wrap($checkbox).check({ force: true });
      cy.log('☑️ 사건번호입력모드 체크 완료');
    });
    
    cy.wait(1000);
    
    // 3. 모든 input 요소 찾아서 사건번호 입력 시도
    cy.get('input[type="text"], input[type="number"]').then($inputs => {
      cy.log(`📝 텍스트 입력 필드 ${$inputs.length}개 발견`);
      
      $inputs.each((index, input) => {
        const id = input.id || '없음';
        const name = input.name || '없음';
        const placeholder = input.placeholder || '없음';
        cy.log(`Input ${index}: id="${id}", name="${name}", placeholder="${placeholder}"`);
        
        // 사건번호로 보이는 필드에 입력 시도
        if (id.includes('sano') || name.includes('sano') || 
            id.includes('case') || name.includes('case') ||
            placeholder.includes('사건') || placeholder.includes('번호')) {
          
          cy.log(`🎯 사건번호 입력 시도: ${id || name}`);
          cy.wrap(input).clear({ force: true });
          cy.wrap(input).type('2024가단12345', { force: true });
          cy.log('📝 사건번호 입력 완료');
        }
      });
    });
    
    cy.wait(1000);
    
    // 4. 검색 버튼 찾기 및 클릭 시도
    const searchSelectors = [
      'button:contains("검색")',
      'input[value*="검색"]',
      'input[type="submit"]',
      '[onclick*="search"]',
      '[onclick*="Search"]',
      '[title*="검색"]'
    ];
    
    let searchFound = false;
    searchSelectors.forEach(selector => {
      cy.get('body').then($body => {
        if ($body.find(selector).length > 0 && !searchFound) {
          cy.log(`🔍 검색 버튼 발견: ${selector}`);
          cy.get(selector).first().click({ force: true });
          cy.log('✅ 검색 실행 완료');
          searchFound = true;
        }
      });
    });
    
    if (!searchFound) {
      cy.log('⚠️ 검색 버튼을 찾지 못함');
    }
    
    cy.wait(3000);
    
    // 5. 결과 확인
    cy.url().then(url => {
      cy.log(`현재 URL: ${url}`);
    });
    
    cy.get('body').then($body => {
      const text = $body.text();
      if (text.includes('사건이 존재하지') || text.includes('검색 결과가 없')) {
        cy.log('📋 검색 결과: 사건 없음');
      } else {
        cy.log('🎯 검색 결과: 다른 페이지 또는 결과 있음');
      }
    });
    
    cy.log('✅ 부분 자동화 테스트 완료');
  });
});

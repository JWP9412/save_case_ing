describe('빠른 요소 확인', function () {
  it('사이트 요소들을 빠르게 확인', function() {
    cy.visit('https://www.scourt.go.kr/portal/information/events/search/search.jsp');
    
    // 페이지 로딩 대기
    cy.wait(3000);
    
    // 검색 관련 요소들 확인
    const elementsToCheck = [
      'input[name="category"]',
      'select[name="category"]', 
      'input[name="dpWord"]',
      'input[id*="search"]',
      'select[id*="search"]',
      'input[type="text"]',
      'button[type="submit"]',
      'input[type="submit"]',
      'button',
      '[onclick*="search"]',
      '[onclick*="Search"]'
    ];
    
    elementsToCheck.forEach(selector => {
      cy.get('body').then($body => {
        const found = $body.find(selector);
        if (found.length > 0) {
          cy.log(`✅ 발견: ${selector} (${found.length}개)`);
          found.each((i, el) => {
            const id = el.id || '없음';
            const name = el.name || '없음';
            const text = el.textContent?.trim()?.substring(0, 20) || '없음';
            cy.log(`   - ${i}: id=${id}, name=${name}, text="${text}"`);
          });
        }
      });
    });
    
    // 모든 input 태그 확인
    cy.get('input').each(($el, index) => {
      const id = $el.attr('id') || '없음';
      const name = $el.attr('name') || '없음';
      const type = $el.attr('type') || '없음';
      const placeholder = $el.attr('placeholder') || '없음';
      cy.log(`Input ${index}: id="${id}", name="${name}", type="${type}", placeholder="${placeholder}"`);
    });
    
    // 모든 select 태그 확인  
    cy.get('select').each(($el, index) => {
      const id = $el.attr('id') || '없음';
      const name = $el.attr('name') || '없음';
      cy.log(`Select ${index}: id="${id}", name="${name}"`);
    });
  });
});

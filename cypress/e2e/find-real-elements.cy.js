describe('실제 요소 찾기', function () {
  it('사건검색 페이지의 실제 요소들 찾기', function() {
    cy.visit('https://www.scourt.go.kr/portal/information/events/search/search.jsp');
    
    // 충분한 로딩 대기
    cy.wait(5000);
    
    // 페이지 제목 확인
    cy.title().then(title => {
      console.log('페이지 제목:', title);
    });
    
    // DOM이 완전히 로드될 때까지 기다림
    cy.get('body').should('be.visible');
    
    // 모든 input 요소들 찾기
    cy.get('input').then($inputs => {
      console.log(`총 ${$inputs.length}개의 input 요소 발견:`);
      $inputs.each((index, input) => {
        const id = input.id || '없음';
        const name = input.name || '없음'; 
        const type = input.type || '없음';
        const placeholder = input.placeholder || '없음';
        const value = input.value || '없음';
        console.log(`Input ${index}: id="${id}", name="${name}", type="${type}", placeholder="${placeholder}", value="${value}"`);
      });
    });
    
    // 모든 select 요소들 찾기
    cy.get('select').then($selects => {
      console.log(`총 ${$selects.length}개의 select 요소 발견:`);
      $selects.each((index, select) => {
        const id = select.id || '없음';
        const name = select.name || '없음';
        console.log(`Select ${index}: id="${id}", name="${name}"`);
      });
    });
    
    // 버튼 요소들 찾기
    cy.get('button, input[type="submit"], input[type="button"]').then($buttons => {
      console.log(`총 ${$buttons.length}개의 버튼 요소 발견:`);
      $buttons.each((index, button) => {
        const id = button.id || '없음';
        const name = button.name || '없음';
        const text = button.textContent?.trim() || button.value || '없음';
        console.log(`Button ${index}: id="${id}", name="${name}", text="${text}"`);
      });
    });
    
    // 특정 텍스트가 포함된 요소들 찾기
    const searchTerms = ['법원', '사건', '검색', '년도', '호', '당사자', '피고'];
    searchTerms.forEach(term => {
      cy.contains(term).then($elements => {
        if ($elements.length > 0) {
          console.log(`"${term}" 텍스트를 포함한 요소들:`);
          $elements.each((index, el) => {
            const tagName = el.tagName;
            const id = el.id || '없음';
            const className = el.className || '없음';
            console.log(`  - ${tagName}: id="${id}", class="${className}"`);
          });
        }
      });
    });
  });
});

describe('Find Current Site Elements', function () {
  it('Should find form elements in current site', function() {
    cy.visit('https://www.scourt.go.kr/portal/information/events/search/search.jsp');
    cy.wait(3000);
    
    // 모든 select 요소 찾기
    cy.get('select').each(($select, index) => {
      cy.log(`Select ${index}: id=${$select.attr('id')}, name=${$select.attr('name')}`);
    });
    
    // 모든 input 요소 찾기  
    cy.get('input').each(($input, index) => {
      const type = $input.attr('type');
      const id = $input.attr('id');
      const name = $input.attr('name');
      cy.log(`Input ${index}: type=${type}, id=${id}, name=${name}`);
    });
    
    // 폼 관련 요소들 찾기
    cy.get('form').should('exist').then(($form) => {
      cy.log(`Found ${$form.length} forms`);
    });
    
    // 버튼 찾기 (더 유연하게)
    cy.get('body').then(($body) => {
      const buttons = $body.find('button, input[type="button"], input[type="submit"], a[onclick], span[onclick], div[onclick]');
      cy.log(`Found ${buttons.length} clickable elements`);
      
      buttons.each((index, btn) => {
        const text = btn.textContent || btn.value || btn.innerHTML;
        const onclick = btn.getAttribute('onclick');
        cy.log(`Clickable ${index}: text="${text.slice(0, 20)}", onclick="${onclick || 'none'}"`);
      });
    });
  });
});

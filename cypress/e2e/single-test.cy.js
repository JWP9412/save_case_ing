describe('단일 실행 테스트', () => {
  it.skip('한 번만 실행되는 사이트 분석', () => {
    cy.log('🔄 단일 실행 테스트 시작');
    
    // 사이트 접속
    cy.visit('https://www.scourt.go.kr/portal/information/events/search/search.jsp');
    
    // 로딩 대기
    cy.wait(5000);
    
    cy.log('✅ 사이트 접속 완료');
    
    // 모든 input 요소 찾기
    cy.get('input').then($inputs => {
      cy.log(`📝 총 ${$inputs.length}개의 input 요소 발견:`);
      $inputs.each((index, input) => {
        const id = input.id || '없음';
        const name = input.name || '없음';
        const type = input.type || '없음';
        const placeholder = input.placeholder || '없음';
        cy.log(`Input ${index}: id="${id}", name="${name}", type="${type}", placeholder="${placeholder}"`);
      });
    });
    
    // 모든 select 요소 찾기
    cy.get('select').then($selects => {
      cy.log(`📋 총 ${$selects.length}개의 select 요소 발견:`);
      $selects.each((index, select) => {
        const id = select.id || '없음';
        const name = select.name || '없음';
        cy.log(`Select ${index}: id="${id}", name="${name}"`);
      });
    });
    
    // 모든 button 요소 찾기 (없을 수 있음)
    cy.get('body').then($body => {
      const buttons = $body.find('button');
      if (buttons.length > 0) {
        cy.log(`🔍 총 ${buttons.length}개의 button 요소 발견:`);
        buttons.each((index, button) => {
          const id = button.id || '없음';
          const text = button.textContent?.trim() || '없음';
          cy.log(`Button ${index}: id="${id}", text="${text}"`);
        });
      } else {
        cy.log('❌ button 요소 없음 - WebSquare 컴포넌트 사용');
      }
      
      // 대신 클릭 가능한 다른 요소들 찾기
      const clickables = $body.find('input[type="submit"], input[type="button"], a[onclick], div[onclick], span[onclick]');
      if (clickables.length > 0) {
        cy.log(`🖱️ 클릭 가능한 요소 ${clickables.length}개 발견:`);
        clickables.each((index, el) => {
          if (index < 10) { // 처음 10개만
            const id = el.id || '없음';
            const tagName = el.tagName;
            const text = el.textContent?.trim() || el.value || '없음';
            const onclick = el.onclick ? 'Y' : 'N';
            cy.log(`Clickable ${index}: ${tagName}, id="${id}", text="${text}", onclick=${onclick}`);
          }
        });
      }
    });
    
    cy.log('✅ 단일 테스트 완료 - 더 이상 실행되지 않음');
  });
});

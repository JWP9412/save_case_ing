describe('정보 수집만', () => {
  it('사이트 요소 정보만 수집하고 끝', () => {
    cy.visit('https://www.scourt.go.kr/portal/information/events/search/search.jsp');
    cy.wait(3000);
    
    // 간단히 input 정보만 수집
    cy.get('input').then($inputs => {
      const inputInfo = [];
      $inputs.each((index, input) => {
        inputInfo.push({
          index,
          id: input.id || '없음',
          name: input.name || '없음',
          type: input.type || '없음'
        });
      });
      
      // 콘솔에 한 번에 출력
      console.log('=== INPUT 요소들 ===');
      inputInfo.forEach(info => {
        console.log(`Input ${info.index}: id="${info.id}", name="${info.name}", type="${info.type}"`);
      });
    });
    
    // select 정보 수집
    cy.get('select').then($selects => {
      const selectInfo = [];
      $selects.each((index, select) => {
        selectInfo.push({
          index,
          id: select.id || '없음',
          name: select.name || '없음'
        });
      });
      
      console.log('=== SELECT 요소들 ===');
      selectInfo.forEach(info => {
        console.log(`Select ${info.index}: id="${info.id}", name="${info.name}"`);
      });
    });
    
    // 테스트 종료
    cy.log('✅ 정보 수집 완료');
  });
});

describe('간단한 자동입력 테스트', function () {
  it('기본적인 자동입력 시도', function() {
    cy.visit('https://www.scourt.go.kr/portal/information/events/search/search.jsp');
    
    // 10초 대기
    cy.wait(10000);
    
    // 모든 select 요소에 대해 시도
    cy.get('select').then($selects => {
      if ($selects.length > 0) {
        // 첫 번째 select에 값 입력 시도
        cy.wrap($selects.first()).select(1, { force: true });
        cy.log('첫 번째 select 입력 시도 완료');
      }
    });
    
    // 모든 input 요소에 대해 시도  
    cy.get('input[type="text"]').then($inputs => {
      if ($inputs.length > 0) {
        // 첫 번째 텍스트 input에 값 입력 시도
        cy.wrap($inputs.first()).type('테스트', { force: true });
        cy.log('첫 번째 input 입력 시도 완료');
      }
    });
    
    // 스크린샷으로 현재 상태 확인
    cy.screenshot('input-test-result');
  });
});



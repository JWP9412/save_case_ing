describe('Debug Site Structure', function () {
  it('Should explore the current site structure', function() {
    cy.visit('https://www.scourt.go.kr/portal/information/events/search/search.jsp');
    
    // 페이지 로딩 대기
    cy.wait(3000);
    
    // 모든 이미지 요소 확인
    cy.get('img').should('exist').then(($imgs) => {
      cy.log(`Found ${$imgs.length} images`);
      $imgs.each((index, img) => {
        cy.log(`Image ${index}: ${img.src || 'no src'}`);
      });
    });
    
    // 숨겨진 요소 포함 모든 div 확인
    cy.get('div').then(($divs) => {
      cy.log(`Found ${$divs.length} divs`);
    });
    
    // 캡챠 관련 요소 찾기
    cy.get('body').then(($body) => {
      if ($body.find('div.sns_m').length > 0) {
        cy.log('Found div.sns_m');
        cy.get('div.sns_m').then(($sns) => {
          cy.log(`sns_m display: ${$sns.css('display')}`);
        });
      } else {
        cy.log('div.sns_m not found');
      }
    });
    
    // 캡챠 입력 필드 찾기
    cy.get('body').then(($body) => {
      const captchaFields = $body.find('input[type="text"]');
      cy.log(`Found ${captchaFields.length} text inputs`);
    });
  });
});

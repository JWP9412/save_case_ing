describe('Simple Network Test', function () {
  it('Should access Google', function() {
    cy.visit('https://www.google.com');
    cy.contains('Google');
  });
  
  it('Should access Naver', function() {
    cy.visit('https://www.naver.com');
    cy.contains('NAVER');
  });
  
  it('Should test court search site', function() {
    // 대법원 검색 페이지 테스트
    cy.visit('https://www.scourt.go.kr/portal/information/events/search/search.jsp');
    cy.contains('사건검색');
  });
});

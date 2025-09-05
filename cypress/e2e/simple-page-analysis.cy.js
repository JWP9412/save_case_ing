describe('간단한 페이지 분석', function () {
  it('현재 페이지의 기본 구조 파악', function() {
    cy.visit('https://www.scourt.go.kr/portal/information/events/search/search.jsp');
    
    // 충분한 로딩 대기
    cy.wait(5000);
    
    // 페이지 기본 정보
    cy.title().then(title => {
      console.log('페이지 제목:', title);
    });
    
    cy.url().then(url => {
      console.log('현재 URL:', url);
    });
    
    // 페이지 전체 텍스트 내용 확인
    cy.get('body').then($body => {
      const pageText = $body.text();
      console.log('페이지 텍스트 길이:', pageText.length);
      
      // 중요한 키워드들 찾기
      const keywords = ['사건', '검색', '조회', '법원', '사건번호', '결과', '없습니다', '존재하지'];
      keywords.forEach(keyword => {
        if (pageText.includes(keyword)) {
          console.log(`✅ "${keyword}" 텍스트 포함됨`);
        }
      });
      
      // 페이지 내용의 일부 출력 (처음 200자)
      console.log('페이지 내용 미리보기:', pageText.substring(0, 200));
    });
    
    // 모든 div 요소 개수 확인
    cy.get('div').then($divs => {
      console.log(`총 ${$divs.length}개의 div 요소`);
    });
    
    // 모든 input 요소 확인
    cy.get('input').then($inputs => {
      console.log(`총 ${$inputs.length}개의 input 요소`);
      if ($inputs.length > 0) {
        $inputs.each((index, input) => {
          if (index < 5) { // 처음 5개만
            console.log(`Input ${index}: type="${input.type}", name="${input.name || '없음'}", id="${input.id || '없음'}"`);
          }
        });
      }
    });
    
    // iframe 확인
    cy.get('body').then($body => {
      const iframes = $body.find('iframe');
      if (iframes.length > 0) {
        console.log(`${iframes.length}개의 iframe 발견`);
        iframes.each((index, iframe) => {
          console.log(`Iframe ${index}: src="${iframe.src || '없음'}"`);
        });
      } else {
        console.log('iframe 없음');
      }
    });
    
    // WebSquare 관련 요소들 찾기
    cy.get('body').then($body => {
      const wsElements = $body.find('[id*="w2"], [class*="w2"], [id*="websquare"], [class*="websquare"]');
      if (wsElements.length > 0) {
        console.log(`${wsElements.length}개의 WebSquare 관련 요소 발견`);
      }
    });
  });
});

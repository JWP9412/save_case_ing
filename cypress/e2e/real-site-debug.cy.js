describe('실제 사이트 구조 정확한 분석', function () {
  it('새로운 대법원 사이트의 실제 구조 파악', function() {
    cy.visit('https://www.scourt.go.kr/portal/information/events/search/search.jsp');
    
    // 충분한 로딩 대기
    cy.wait(15000);
    cy.log('🔍 15초 로딩 대기 완료');
    
    // 페이지 전체 HTML 구조 로깅
    cy.get('body').then($body => {
      cy.log('=== 페이지 전체 구조 분석 시작 ===');
      
      // 모든 form 찾기
      const forms = $body.find('form');
      cy.log(`📋 총 ${forms.length}개의 form 발견`);
      
      forms.each((index, form) => {
        const id = form.id || '없음';
        const action = form.action || '없음';
        const method = form.method || 'GET';
        cy.log(`Form ${index}: id="${id}", action="${action}", method="${method}"`);
        
        // 각 form 내부의 input과 select 찾기
        const inputs = $(form).find('input, select');
        cy.log(`  └ 내부 input/select: ${inputs.length}개`);
        
        inputs.each((i, input) => {
          if (i < 5) { // 처음 5개만
            const tagName = input.tagName;
            const id = input.id || '없음';
            const name = input.name || '없음';
            const type = input.type || '없음';
            const title = input.title || '없음';
            const placeholder = input.placeholder || '없음';
            cy.log(`    ${i}: ${tagName} id="${id}" name="${name}" type="${type}" title="${title}" placeholder="${placeholder}"`);
          }
        });
      });
      
      // iframe 확인
      const iframes = $body.find('iframe');
      if (iframes.length > 0) {
        cy.log(`🖼️ ${iframes.length}개의 iframe 발견:`);
        iframes.each((index, iframe) => {
          const src = iframe.src || '없음';
          const id = iframe.id || '없음';
          const name = iframe.name || '없음';
          cy.log(`Iframe ${index}: id="${id}", name="${name}", src="${src}"`);
        });
      }
      
      // 사건검색과 관련된 텍스트 근처 요소들 찾기
      const searchTexts = ['사건검색', '법원', '사건번호', '당사자', '년도', '사건종류'];
      searchTexts.forEach(text => {
        if ($body.text().includes(text)) {
          cy.log(`🎯 "${text}" 텍스트 발견됨`);
        }
      });
      
      // WebSquare 관련 요소들
      const wsElements = $body.find('[id*="w2"], [class*="w2"], [id*="websquare"], [id*="mf_"], [id*="ssgo"]');
      cy.log(`⚡ ${wsElements.length}개의 WebSquare/SSGO 관련 요소 발견`);
      
      wsElements.each((index, element) => {
        if (index < 20) { // 처음 20개만
          const tagName = element.tagName;
          const id = element.id || '없음';
          const className = element.className || '없음';
          cy.log(`WS ${index}: ${tagName} id="${id}" class="${className}"`);
        }
      });
    });
    
    // 실제로 보이는 input과 select만 찾기
    cy.get('input:visible, select:visible').then($visibleElements => {
      cy.log(`👀 실제로 보이는 input/select: ${$visibleElements.length}개`);
      
      $visibleElements.each((index, element) => {
        if (index < 10) { // 처음 10개만
          const tagName = element.tagName;
          const id = element.id || '없음';
          const name = element.name || '없음';
          const type = element.type || '없음';
          const title = element.title || '없음';
          const placeholder = element.placeholder || '없음';
          const value = element.value || '없음';
          cy.log(`Visible ${index}: ${tagName} id="${id}" name="${name}" type="${type}" title="${title}" placeholder="${placeholder}" value="${value}"`);
        }
      });
    });
    
    // 최종 스크린샷
    cy.screenshot('real-site-structure');
    cy.log('=== 분석 완료 ===');
  });
});



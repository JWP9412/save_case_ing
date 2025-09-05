describe('검색 결과 페이지 요소 찾기', function () {
  it('새 사이트의 검색 결과 페이지 구조 파악', function() {
    cy.visit('https://www.scourt.go.kr/portal/information/events/search/search.jsp');
    
    // 충분한 로딩 대기
    cy.wait(5000);
    
    // 페이지 제목 확인
    cy.title().then(title => {
      cy.log(`현재 페이지: ${title}`);
    });
    
    // URL 확인
    cy.url().then(url => {
      cy.log(`현재 URL: ${url}`);
    });
    
    // 모든 테이블 요소 찾기 (있는 경우)
    cy.get('body').then($body => {
      const tables = $body.find('table');
      if (tables.length > 0) {
        cy.log(`총 ${tables.length}개의 테이블 발견:`);
        tables.each((index, table) => {
          const id = table.id || '없음';
          const className = table.className || '없음';
          cy.log(`Table ${index}: id="${id}", class="${className}"`);
        });
      } else {
        cy.log('❌ 테이블 요소 없음 - 다른 구조 사용');
      }
    });
    
    // 모든 버튼 요소 찾기
    cy.get('button, input[type="button"], input[type="submit"], a').then($buttons => {
      cy.log(`총 ${$buttons.length}개의 클릭 가능한 요소 발견:`);
      $buttons.each((index, btn) => {
        const id = btn.id || '없음';
        const className = btn.className || '없음';
        const text = btn.textContent?.trim() || btn.value || '없음';
        const tagName = btn.tagName;
        cy.log(`${tagName} ${index}: id="${id}", class="${className}", text="${text}"`);
      });
    });
    
    // 빨간색 스타일의 요소들 찾기
    cy.get('[class*="red"], [style*="red"], [style*="Red"]').then($redElements => {
      if ($redElements.length > 0) {
        cy.log(`빨간색 관련 요소 ${$redElements.length}개 발견:`);
        $redElements.each((index, el) => {
          const id = el.id || '없음';
          const className = el.className || '없음';
          const tagName = el.tagName;
          const text = el.textContent?.trim()?.substring(0, 20) || '없음';
          cy.log(`Red ${index}: ${tagName}, id="${id}", class="${className}", text="${text}"`);
        });
      }
    });
    
    // 특정 텍스트를 포함한 요소들 찾기
    const searchTerms = ['조회', '검색', '상세', '결과', '존재하지', '없습니다', '사건'];
    searchTerms.forEach(term => {
      cy.get('body').then($body => {
        if ($body.text().includes(term)) {
          cy.log(`"${term}" 텍스트 포함된 페이지`);
          cy.contains(term).then($elements => {
            if ($elements.length > 0) {
              $elements.each((index, el) => {
                const tagName = el.tagName;
                const id = el.id || '없음';
                const className = el.className || '없음';
                cy.log(`  "${term}" 요소 ${index}: ${tagName}, id="${id}", class="${className}"`);
              });
            }
          });
        }
      });
    });
    
    // div 요소들 중 중요해 보이는 것들 찾기
    cy.get('div[class*="table"], div[class*="result"], div[class*="content"]').then($divs => {
      if ($divs.length > 0) {
        cy.log(`결과 관련 div 요소 ${$divs.length}개 발견:`);
        $divs.each((index, div) => {
          const id = div.id || '없음';
          const className = div.className || '없음';
          cy.log(`Result div ${index}: id="${id}", class="${className}"`);
        });
      }
    });
    
    // iframe이 있는지 확인
    cy.get('iframe').then($iframes => {
      if ($iframes.length > 0) {
        cy.log(`${$iframes.length}개의 iframe 발견 - 결과가 iframe 내부에 있을 수 있음`);
        $iframes.each((index, iframe) => {
          const src = iframe.src || '없음';
          const id = iframe.id || '없음';
          cy.log(`Iframe ${index}: id="${id}", src="${src}"`);
        });
      }
    });
  });
});

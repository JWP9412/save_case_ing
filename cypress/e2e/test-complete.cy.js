describe('완전한 사건검색 테스트', () => {
  it('사건번호 입력부터 검색까지 완료', () => {
    // 새 사이트 접속
    cy.visit('https://www.scourt.go.kr/portal/information/events/search/search.jsp');
    
    // 로딩 대기
    cy.wait(8000);
    
    // 페이지 제목 확인
    cy.title().should('include', '사건검색');
    cy.log('✅ 사이트 접속 성공');
    
    // 실제 발견된 입력 필드 사용
    cy.get('#search_word').should('exist');
    cy.log('✅ search_word 입력 필드 발견');
    
    // 테스트 데이터 입력
    cy.get('#search_word').clear({ force: true });
    cy.get('#search_word').type('2024가단1234', { force: true });
    cy.log('📝 사건번호 입력 완료: 2024가단1234');
    
    cy.wait(1000);
    
    // 더 다양한 검색 버튼 찾기
    const searchButtons = [
      // 일반적인 버튼들
      'button:contains("검색")',
      'button:contains("조회")',
      'input[type="submit"]',
      'input[value*="검색"]',
      'input[value*="조회"]',
      // WebSquare 패턴들
      'button[id*="search"]',
      'button[id*="Search"]',
      'input[id*="search"]',
      'input[id*="Search"]',
      'a[id*="search"]',
      'a[id*="Search"]',
      // onclick 이벤트가 있는 요소들
      '[onclick*="search"]',
      '[onclick*="Search"]',
      '[onclick*="submit"]',
      '[onclick*="find"]',
      '[onclick*="query"]',
      // 일반적인 클래스명들
      '.searchBtn',
      '.search-btn',
      '.btn-search',
      '.search_btn'
    ];
    
    let searchExecuted = false;
    
    // 각 선택자 시도
    searchButtons.forEach(selector => {
      cy.get('body').then($body => {
        if ($body.find(selector).length > 0 && !searchExecuted) {
          cy.log(`✅ 검색 버튼 발견: ${selector}`);
          
          // 버튼 정보 확인
          cy.get(selector).first().then($btn => {
            const text = $btn.text() || $btn.val() || '텍스트없음';
            const id = $btn.attr('id') || '없음';
            const className = $btn.attr('class') || '없음';
            cy.log(`버튼 정보: text="${text}", id="${id}", class="${className}"`);
            
            // 클릭 시도
            cy.wrap($btn).click({ force: true });
            cy.log('🔍 검색 버튼 클릭 완료');
            searchExecuted = true;
          });
        }
      });
    });
    
    // 검색 버튼이 없다면 Enter 키 시도
    cy.get('body').then($body => {
      if (!searchExecuted) {
        cy.log('⚠️ 검색 버튼을 찾지 못함 - Enter 키 시도');
        cy.get('#search_word').type('{enter}', { force: true });
        cy.log('⌨️ Enter 키 입력 완료');
        searchExecuted = true;
      }
    });
    
    // 검색 결과 대기
    cy.wait(5000);
    
    // URL 변경 확인
    cy.url().then(url => {
      cy.log(`현재 URL: ${url}`);
    });
    
    // 페이지 제목 변경 확인
    cy.title().then(title => {
      cy.log(`현재 페이지 제목: ${title}`);
    });
    
    // 결과 페이지 분석
    cy.get('body').then($body => {
      const pageText = $body.text();
      
      // 사건이 없는 경우들
      const noResultPatterns = [
        '사건이 존재하지 않습니다',
        '검색 결과가 없습니다',
        '조회된 내용이 없습니다',
        '해당하는 사건이 없습니다',
        '검색된 사건이 없습니다',
        '검색결과가 없습니다'
      ];
      
      // 사건이 있는 경우들
      const hasResultPatterns = [
        '사건정보',
        '사건현황',
        '진행상황',
        '사건내역',
        '판결문',
        '결정문'
      ];
      
      const hasNoResult = noResultPatterns.some(pattern => pageText.includes(pattern));
      const hasResult = hasResultPatterns.some(pattern => pageText.includes(pattern));
      
      if (hasNoResult) {
        cy.log('📋 검색 결과: 사건이 존재하지 않음');
      } else if (hasResult) {
        cy.log('🎯 검색 결과: 사건 정보 발견!');
        
        // 스크린샷 촬영
        cy.screenshot('case-search-result', {
          onAfterScreenshot($el, props) {
            cy.log(`📸 스크린샷 저장: ${props.name}`);
          }
        });
      } else {
        cy.log('❓ 검색 결과: 알 수 없는 상태');
        cy.log(`페이지 내용 미리보기: ${pageText.substring(0, 200)}...`);
      }
    });
    
    cy.log('✅ 완전한 테스트 완료');
  });
});

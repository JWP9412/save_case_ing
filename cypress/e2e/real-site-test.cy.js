describe('실제 사이트 구조 기반 테스트', () => {
  // 2번만 실행되도록 제한
  let executionCount = 0;
  const maxExecutions = 2;
  
  it('정확한 요소들로 사건검색 실행', () => {
    // 실행 횟수 체크
    executionCount++;
    if (executionCount > maxExecutions) {
      cy.log(`⏹️ 최대 실행 횟수(${maxExecutions})에 도달하여 건너뜀`);
      return;
    }
    
    cy.log(`🔄 실행 횟수: ${executionCount}/${maxExecutions}`);
    // 사이트 접속
    cy.visit('https://www.scourt.go.kr/portal/information/events/search/search.jsp');
    
    // 충분한 로딩 대기
    cy.wait(8000);
    
    cy.log('✅ 사이트 접속 완료');
    
    // 1. 법원 선택 드롭다운 찾기 (성남지원 등)
    cy.get('body').then($body => {
      // 드롭다운 옵션들 찾기
      const dropdownSelectors = [
        'select',
        'select[name*="court"]',
        'select[name*="bub"]',
        'select[id*="court"]',
        'select[id*="bub"]'
      ];
      
      dropdownSelectors.forEach(selector => {
        const elements = $body.find(selector);
        if (elements.length > 0) {
          cy.log(`✅ 드롭다운 발견: ${selector}`);
          elements.each((index, el) => {
            const id = el.id || '없음';
            const name = el.name || '없음';
            const optionsCount = el.options ? el.options.length : 0;
            cy.log(`  Dropdown ${index}: id="${id}", name="${name}", options=${optionsCount}`);
          });
        }
      });
    });
    
    // 2. 사건번호 입력 필드 찾기 (37574가 입력된 곳)
    cy.get('body').then($body => {
      // 숫자가 입력될 수 있는 필드들 찾기
      const numberInputSelectors = [
        'input[type="text"]',
        'input[type="number"]',
        'input[maxlength]',
        'input[name*="case"]',
        'input[name*="sa"]',
        'input[name*="number"]',
        'input[id*="case"]',
        'input[id*="sa"]',
        'input[id*="number"]'
      ];
      
      numberInputSelectors.forEach(selector => {
        const elements = $body.find(selector);
        if (elements.length > 0) {
          cy.log(`✅ 입력 필드 발견: ${selector}`);
          elements.each((index, el) => {
            const id = el.id || '없음';
            const name = el.name || '없음';
            const placeholder = el.placeholder || '없음';
            const maxLength = el.maxLength || '없음';
            cy.log(`  Input ${index}: id="${id}", name="${name}", placeholder="${placeholder}", maxLength=${maxLength}`);
          });
        }
      });
    });
    
    // 3. 검색 버튼 찾기 (🔍 검색)
    cy.get('body').then($body => {
      const buttonSelectors = [
        'button',
        'input[type="submit"]',
        'input[type="button"]',
        'a[role="button"]'
      ];
      
      buttonSelectors.forEach(selector => {
        const elements = $body.find(selector);
        if (elements.length > 0) {
          cy.log(`✅ 버튼 요소 발견: ${selector}`);
          elements.each((index, el) => {
            const id = el.id || '없음';
            const text = el.textContent?.trim() || el.value || '없음';
            const onclick = el.onclick ? 'Y' : 'N';
            cy.log(`  Button ${index}: id="${id}", text="${text}", onclick=${onclick}`);
          });
        }
      });
    });
    
    // 4. 실제 입력 시도 (가장 적절한 필드에)
    cy.log('🔍 사건번호 입력 시도...');
    
    // 일반적인 텍스트 입력 필드들 시도
    const testInputSelectors = [
      'input[type="text"]',
      'input[type="number"]',
      'input[maxlength="5"]',  // 사건번호는 보통 5자리
      'input[maxlength="6"]'
    ];
    
    let inputSuccess = false;
    testInputSelectors.forEach(selector => {
      cy.get('body').then($body => {
        if ($body.find(selector).length > 0 && !inputSuccess) {
          cy.get(selector).first().then($input => {
            // 숫자만 입력 가능한 필드인지 확인
            const maxLen = $input.attr('maxlength');
            const inputType = $input.attr('type');
            
            if ((maxLen && parseInt(maxLen) <= 10) || inputType === 'number') {
              cy.log(`📝 사건번호 입력 시도: ${selector}`);
              cy.wrap($input).clear({ force: true });
              cy.wrap($input).type('12345', { force: true }); // 테스트 번호
              cy.log('✅ 사건번호 입력 완료');
              inputSuccess = true;
            }
          });
        }
      });
    });
    
    cy.wait(1000);
    
    // 5. 검색 버튼 클릭 시도
    cy.log('🔍 검색 버튼 클릭 시도...');
    
    const searchButtonSelectors = [
      'button:contains("검색")',
      'input[value*="검색"]',
      'button[title*="검색"]',
      '[onclick*="search"]',
      '[onclick*="Search"]'
    ];
    
    let searchSuccess = false;
    searchButtonSelectors.forEach(selector => {
      cy.get('body').then($body => {
        if ($body.find(selector).length > 0 && !searchSuccess) {
          cy.log(`🔍 검색 버튼 클릭: ${selector}`);
          cy.get(selector).first().click({ force: true });
          searchSuccess = true;
        }
      });
    });
    
    // 검색 버튼이 없으면 Enter 키 시도
    if (!searchSuccess) {
      cy.log('⌨️ Enter 키로 검색 시도');
      cy.get('input[type="text"]').first().type('{enter}', { force: true });
    }
    
    // 6. 결과 확인
    cy.wait(3000);
    
    cy.url().then(url => {
      cy.log(`현재 URL: ${url}`);
    });
    
    cy.get('body').then($body => {
      const text = $body.text();
      cy.log(`페이지 내용 일부: ${text.substring(0, 200)}...`);
    });
    
    cy.log('✅ 실제 구조 테스트 완료');
  });
});

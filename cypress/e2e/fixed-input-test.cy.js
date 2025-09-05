describe('수정된 자동입력 테스트', function () {
  it('올바른 사건 검색 폼에 자동입력', function() {
    cy.visit('https://www.scourt.go.kr/portal/information/events/search/search.jsp');
    
    // WebSquare 로딩 대기
    cy.wait(10000);
    cy.log('🔍 WebSquare 로딩 완료');
    
    // 상단 검색바가 아닌 실제 사건 검색 폼 찾기
    cy.log('🎯 사건 검색 폼 찾는 중...');
    
    // 1. 법원 선택 드롭다운 찾기 (상단 검색바 제외)
    const courtSelectors = [
      '#mf_ssgoTopMainTab_contents_content1_body_sbx_cortCd',
      'select[title*="법원"]:not(#search_total)',
      'select[class*="w2selectbox"]',
      'select:not(.searchSelect):not(#search_total)'
    ];
    
    let foundCourt = false;
    
    courtSelectors.forEach((selector, index) => {
      cy.get('body').then($body => {
        if ($body.find(selector).length > 0 && !foundCourt) {
          cy.log(`✅ 법원 드롭다운 발견: ${selector}`);
          foundCourt = true;
          
          cy.get(selector).first().then($select => {
            const optionsText = [];
            $select.find('option').each((i, option) => {
              optionsText.push(option.text);
            });
            cy.log(`📋 법원 옵션들: ${optionsText.join(', ')}`);
            
            // 서울중앙지방법원 선택 시도
            if (optionsText.includes('서울중앙지방법원')) {
              cy.wrap($select).select('서울중앙지방법원', { force: true });
              cy.log('✅ 서울중앙지방법원 선택 성공!');
            } else {
              cy.log('⚠️ 서울중앙지방법원 옵션이 없음');
            }
          });
        }
      });
    });
    
    // 2. 사건번호 입력 필드 찾기 (상단 검색바 제외)
    const caseInputSelectors = [
      '#mf_ssgoTopMainTab_contents_content1_body_ibx_sano',
      'input[title*="사건번호"]:not(#search_word)',
      'input[placeholder*="사건번호"]',
      'input[type="text"]:not(.searchInput):not(#search_word)'
    ];
    
    let foundInput = false;
    
    caseInputSelectors.forEach((selector, index) => {
      cy.get('body').then($body => {
        if ($body.find(selector).length > 0 && !foundInput) {
          cy.log(`✅ 사건번호 입력 필드 발견: ${selector}`);
          foundInput = true;
          
          cy.get(selector).first().then($input => {
            const placeholder = $input.attr('placeholder') || '';
            const title = $input.attr('title') || '';
            cy.log(`📝 입력 필드 정보: placeholder="${placeholder}", title="${title}"`);
            
            cy.wrap($input).clear().type('2024가합51101', { force: true });
            cy.log('✅ 사건번호 입력 성공!');
          });
        }
      });
    });
    
    // 3. 당사자명 입력 필드 찾기
    const partyInputSelectors = [
      '#mf_ssgoTopMainTab_contents_content1_body_ibx_dsNm',
      'input[title*="당사자"]',
      'input[placeholder*="당사자"]'
    ];
    
    partyInputSelectors.forEach((selector, index) => {
      cy.get('body').then($body => {
        if ($body.find(selector).length > 0) {
          cy.log(`✅ 당사자명 입력 필드 발견: ${selector}`);
          
          cy.get(selector).first().then($input => {
            cy.wrap($input).clear().type('신안', { force: true });
            cy.log('✅ 당사자명 입력 성공!');
          });
        }
      });
    });
    
    // 최종 상태 스크린샷
    cy.wait(2000);
    cy.screenshot('fixed-input-result');
    cy.log('📸 수정된 자동입력 테스트 완료');
  });
});



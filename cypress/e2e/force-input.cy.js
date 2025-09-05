describe('강제 자동입력 테스트', function () {
  it('숨겨진 요소들에 강제로 입력하기', function() {
    cy.visit('https://www.scourt.go.kr/portal/information/events/search/search.jsp');
    
    // 충분한 로딩 대기
    cy.wait(15000);
    cy.log('🔍 15초 로딩 완료');
    
    // 모든 요소를 force로 찾아서 입력 시도
    cy.get('body').then($body => {
      
      // 1. 모든 select 요소에 강제 접근
      const allSelects = $body.find('select');
      cy.log(`📋 총 ${allSelects.length}개 select 발견, 강제 접근 시도`);
      
      allSelects.each((index, select) => {
        const id = select.id || '없음';
        const optionsCount = select.options.length;
        
        cy.log(`Select ${index}: id="${id}", options=${optionsCount}`);
        
        // 법원 선택 시도 (옵션이 많은 드롭다운)
        if (optionsCount > 5) {
          cy.log(`🎯 법원 드롭다운으로 추정: ${id}`);
          
          // 옵션 목록 확인
          const options = [];
          for (let i = 0; i < Math.min(10, optionsCount); i++) {
            options.push(select.options[i].text);
          }
          cy.log(`  옵션들: ${options.join(', ')}`);
          
          // 서울중앙지방법원 찾아서 선택
          for (let i = 0; i < optionsCount; i++) {
            if (select.options[i].text.includes('서울중앙')) {
              cy.log(`✅ 서울중앙지방법원 발견: 인덱스 ${i}`);
              cy.wrap(select).select(i, { force: true });
              break;
            }
          }
        }
        
        // 년도 선택 시도 (2025가 있는 드롭다운)
        else if (optionsCount > 2 && optionsCount < 10) {
          const options = [];
          for (let i = 0; i < optionsCount; i++) {
            options.push(select.options[i].text);
          }
          
          if (options.includes('2024')) {
            cy.log(`🗓️ 년도 드롭다운으로 추정: ${id}`);
            cy.log(`  옵션들: ${options.join(', ')}`);
            cy.wrap(select).select('2024', { force: true });
          }
        }
      });
      
      // 2. 모든 input 요소에 강제 접근
      const allInputs = $body.find('input[type="text"]');
      cy.log(`📝 총 ${allInputs.length}개 text input 발견, 강제 접근 시도`);
      
      allInputs.each((index, input) => {
        const id = input.id || '없음';
        const name = input.name || '없음';
        const maxLength = input.maxLength;
        const placeholder = input.placeholder || '';
        
        cy.log(`Input ${index}: id="${id}", name="${name}", maxLength=${maxLength}, placeholder="${placeholder}"`);
        
        // 사건번호 입력 시도 (길이 제한이 있는 것)
        if (maxLength === 7 || maxLength === 6 || id.includes('serial') || name.includes('serial')) {
          cy.log(`🔢 사건번호 입력으로 추정: ${id}`);
          cy.wrap(input).clear({ force: true });
          cy.wrap(input).type('51101', { force: true });
        }
        
        // 당사자명 입력 시도 (길이가 긴 것)
        else if (maxLength > 10 || id.includes('name') || id.includes('nm') || name.includes('name')) {
          cy.log(`👤 당사자명 입력으로 추정: ${id}`);
          cy.wrap(input).clear({ force: true });
          cy.wrap(input).type('신안', { force: true });
        }
        
        // 일반적인 텍스트 입력 시도
        else if (maxLength === -1 || maxLength > 5) {
          cy.log(`📄 일반 텍스트 입력: ${id}`);
          cy.wrap(input).clear({ force: true });
          cy.wrap(input).type('테스트입력', { force: true });
        }
      });
      
      // 3. 체크박스 시도
      const checkboxes = $body.find('input[type="checkbox"]');
      cy.log(`☑️ 총 ${checkboxes.length}개 checkbox 발견`);
      
      checkboxes.each((index, checkbox) => {
        const id = checkbox.id || '없음';
        cy.log(`Checkbox ${index}: id="${id}"`);
        
        if (id.includes('사건번호') || id.includes('input') || id.includes('mode')) {
          cy.log(`✅ 사건번호 모드 체크박스로 추정: ${id}`);
          cy.wrap(checkbox).check({ force: true });
        }
      });
    });
    
    // 잠시 대기 후 스크린샷
    cy.wait(3000);
    cy.screenshot('force-input-result');
    cy.log('🎯 강제 입력 테스트 완료');
  });
});



describe('수동 디버그 - 실제 요소 찾기', function () {
  it('실제 사건 검색 폼 요소들을 정확히 찾기', function() {
    cy.visit('https://www.scourt.go.kr/portal/information/events/search/search.jsp');
    
    // 충분한 로딩 대기
    cy.wait(15000);
    cy.log('🔍 15초 로딩 완료');
    
    // 모든 요소 실시간 확인
    cy.get('body').then($body => {
      cy.log('=== 실제 사용 가능한 요소들 찾기 ===');
      
      // 1. 모든 select 요소 확인
      const allSelects = $body.find('select');
      cy.log(`📋 총 ${allSelects.length}개 select 발견:`);
      
      allSelects.each((index, select) => {
        const id = select.id || '없음';
        const name = select.name || '없음';
        const title = select.title || '없음';
        const className = select.className || '없음';
        const optionsCount = select.options.length;
        const isVisible = select.offsetParent !== null;
        
        cy.log(`Select ${index}: id="${id}", name="${name}", title="${title}", class="${className}", options=${optionsCount}, visible=${isVisible}`);
        
        // 옵션들도 확인
        if (optionsCount > 0) {
          const options = [];
          for (let i = 0; i < Math.min(5, optionsCount); i++) {
            options.push(select.options[i].text);
          }
          cy.log(`  옵션들: ${options.join(', ')}`);
        }
      });
      
      // 2. 모든 input 요소 확인 (type="text")
      const allInputs = $body.find('input[type="text"]');
      cy.log(`📝 총 ${allInputs.length}개 text input 발견:`);
      
      allInputs.each((index, input) => {
        const id = input.id || '없음';
        const name = input.name || '없음';
        const title = input.title || '없음';
        const placeholder = input.placeholder || '없음';
        const className = input.className || '없음';
        const maxLength = input.maxLength || '없음';
        const isVisible = input.offsetParent !== null;
        
        cy.log(`Input ${index}: id="${id}", name="${name}", title="${title}", placeholder="${placeholder}", class="${className}", maxLength=${maxLength}, visible=${isVisible}`);
      });
      
      // 3. 체크박스 확인
      const checkboxes = $body.find('input[type="checkbox"]');
      cy.log(`☑️ 총 ${checkboxes.length}개 checkbox 발견:`);
      
      checkboxes.each((index, checkbox) => {
        const id = checkbox.id || '없음';
        const name = checkbox.name || '없음';
        const title = checkbox.title || '없음';
        const isVisible = checkbox.offsetParent !== null;
        
        cy.log(`Checkbox ${index}: id="${id}", name="${name}", title="${title}", visible=${isVisible}`);
      });
    });
    
    // 실제 자동입력 시도하면서 로깅
    cy.log('🎯 실제 자동입력 시도 시작...');
    
    // 페이지에서 "법원" 텍스트 근처 찾기
    cy.contains('법원').then($element => {
      cy.log('📍 "법원" 텍스트 발견됨');
      
      // 근처의 select 찾기
      const $parent = $element.parent();
      const $nearbySelects = $parent.find('select');
      
      if ($nearbySelects.length > 0) {
        cy.log(`✅ "법원" 근처에 ${$nearbySelects.length}개 select 발견`);
        
        $nearbySelects.each((index, select) => {
          const id = select.id || '없음';
          const options = [];
          for (let i = 0; i < Math.min(3, select.options.length); i++) {
            options.push(select.options[i].text);
          }
          cy.log(`  Select ${index}: id="${id}", 첫 옵션들: ${options.join(', ')}`);
          
          // 실제 선택 시도
          if (select.options.length > 1) {
            cy.wrap(select).select(1, { force: true }).then(() => {
              cy.log(`✅ Select ${index} 자동선택 성공!`);
            }).catch(err => {
              cy.log(`❌ Select ${index} 자동선택 실패: ${err.message}`);
            });
          }
        });
      }
    });
    
    // 최종 스크린샷
    cy.wait(3000);
    cy.screenshot('manual-debug-result');
    cy.log('🎯 수동 디버그 완료');
  });
});



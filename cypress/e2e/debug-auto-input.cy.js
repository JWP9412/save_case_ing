describe('자동입력 디버그 테스트', function () {
  it('자동입력이 안 되는 원인 분석', function() {
    cy.visit('https://www.scourt.go.kr/portal/information/events/search/search.jsp');
    
    // 충분한 로딩 대기
    cy.wait(10000);
    cy.log('🔍 페이지 로딩 완료, 요소 분석 시작');
    
    // 1. 페이지가 완전히 로드되었는지 확인
    cy.get('body').should('be.visible');
    cy.log('✅ 페이지 body 로딩 확인');
    
    // 2. iframe이 있는지 확인
    cy.get('body').then($body => {
      const iframes = $body.find('iframe');
      if (iframes.length > 0) {
        cy.log(`⚠️ ${iframes.length}개의 iframe 발견 - 자동입력이 iframe 내부에 있을 수 있음`);
        iframes.each((index, iframe) => {
          const src = iframe.src || '없음';
          const id = iframe.id || '없음';
          cy.log(`Iframe ${index}: id="${id}", src="${src}"`);
        });
      } else {
        cy.log('✅ iframe 없음 - 직접 접근 가능');
      }
    });
    
    // 3. WebSquare 관련 요소들 확인
    cy.get('body').then($body => {
      const wsElements = $body.find('[id*="w2"], [class*="w2"], [id*="websquare"]');
      if (wsElements.length > 0) {
        cy.log(`🔧 ${wsElements.length}개의 WebSquare 요소 발견`);
      }
    });
    
    // 4. 모든 select 요소 찾기
    cy.get('body').then($body => {
      const allSelects = $body.find('select');
      cy.log(`📋 총 ${allSelects.length}개의 select 요소 발견:`);
      
      allSelects.each((index, select) => {
        const id = select.id || '없음';
        const name = select.name || '없음';
        const title = select.title || '없음';
        const visible = select.offsetParent !== null ? 'Y' : 'N';
        const disabled = select.disabled ? 'Y' : 'N';
        cy.log(`Select ${index}: id="${id}", name="${name}", title="${title}", visible=${visible}, disabled=${disabled}`);
      });
    });
    
    // 5. 모든 input 요소 찾기
    cy.get('body').then($body => {
      const allInputs = $body.find('input');
      cy.log(`📝 총 ${allInputs.length}개의 input 요소 발견:`);
      
      allInputs.each((index, input) => {
        if (index < 20) { // 처음 20개만
          const id = input.id || '없음';
          const name = input.name || '없음';
          const type = input.type || '없음';
          const placeholder = input.placeholder || '없음';
          const visible = input.offsetParent !== null ? 'Y' : 'N';
          const disabled = input.disabled ? 'Y' : 'N';
          const readonly = input.readOnly ? 'Y' : 'N';
          cy.log(`Input ${index}: id="${id}", name="${name}", type="${type}", placeholder="${placeholder}", visible=${visible}, disabled=${disabled}, readonly=${readonly}`);
        }
      });
    });
    
    // 6. 실제 자동입력 시도
    cy.log('🎯 실제 자동입력 시도 시작...');
    
    // 법원 선택 시도
    const courtSelectors = [
      '#mf_ssgoTopMainTab_contents_content1_body_sbx_cortCd',
      'select[title*="법원"]',
      'select[class*="w2selectbox"]',
      'select:first'
    ];
    
    let foundAnySelect = false;
    courtSelectors.forEach((selector, index) => {
      cy.get('body').then($body => {
        if ($body.find(selector).length > 0) {
          cy.log(`✅ 선택자 ${index} 발견: ${selector}`);
          foundAnySelect = true;
          
          cy.get(selector).first().then($select => {
            const isVisible = $select.is(':visible');
            const isDisabled = $select.is(':disabled');
            const hasOptions = $select.find('option').length;
            
            cy.log(`   - 보임: ${isVisible}, 비활성: ${isDisabled}, 옵션수: ${hasOptions}`);
            
            if (isVisible && !isDisabled && hasOptions > 0) {
              cy.log('   🔥 자동입력 시도!');
              cy.wrap($select).select('서울중앙지방법원', { force: true }).then(() => {
                cy.log('   ✅ 자동입력 성공!');
              }).catch(() => {
                cy.log('   ❌ 자동입력 실패');
              });
            } else {
              cy.log('   ⚠️ 자동입력 불가능한 상태');
            }
          });
        }
      });
    });
    
    cy.then(() => {
      if (!foundAnySelect) {
        cy.log('❌ 어떤 select 요소도 찾을 수 없음');
      }
    });
    
    // 7. JavaScript 에러 확인
    cy.window().then((win) => {
      cy.log('🔍 JavaScript 에러 확인...');
      // 콘솔 에러가 있는지 확인
    });
  });
});



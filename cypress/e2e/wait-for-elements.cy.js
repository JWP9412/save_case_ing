describe('요소 로딩 대기 테스트', function () {
  it('WebSquare 요소들이 완전히 로딩될 때까지 대기', function() {
    cy.visit('https://www.scourt.go.kr/portal/information/events/search/search.jsp');
    
    // 기본 대기
    cy.wait(10000);
    cy.log('🔍 10초 기본 대기 완료');
    
    // WebSquare 요소들이 로딩될 때까지 반복 체크
    cy.log('⏳ WebSquare 요소 로딩 대기 중...');
    
    // 사건 검색 관련 요소가 나타날 때까지 최대 60초 대기
    const checkForElements = () => {
      cy.get('body').then($body => {
        const allInputs = $body.find('input');
        const allSelects = $body.find('select');
        const visibleInputs = $body.find('input:visible');
        const visibleSelects = $body.find('select:visible');
        
        cy.log(`📊 현재 상태: input=${allInputs.length}(${visibleInputs.length}개 보임), select=${allSelects.length}(${visibleSelects.length}개 보임)`);
        
        // WebSquare 관련 요소들 확인
        const wsElements = $body.find('[id*="mf_"], [id*="ssgo"], [class*="w2"]');
        cy.log(`⚡ WebSquare 요소: ${wsElements.length}개`);
        
        // 사건 검색과 관련된 특정 텍스트들이 있는지 확인
        const hasKeywords = ['사건번호', '당사자', '법원'].some(keyword => 
          $body.text().includes(keyword)
        );
        
        if (hasKeywords) {
          cy.log('✅ 사건 검색 관련 텍스트 발견됨!');
        } else {
          cy.log('⚠️ 사건 검색 관련 텍스트가 아직 없음');
        }
        
        // 더 구체적인 요소들 찾기
        allInputs.each((index, input) => {
          const id = input.id || '없음';
          const name = input.name || '없음';
          const type = input.type || '없음';
          const visible = input.offsetParent !== null;
          
          if (id.includes('mf_') || id.includes('ssgo') || id.includes('사건') || id.includes('법원')) {
            cy.log(`🎯 관련 input 발견: id="${id}", name="${name}", type="${type}", visible=${visible}`);
          }
        });
        
        allSelects.each((index, select) => {
          const id = select.id || '없음';
          const name = select.name || '없음';
          const visible = select.offsetParent !== null;
          const optionsCount = select.options.length;
          
          if (id.includes('mf_') || id.includes('ssgo') || id.includes('법원') || optionsCount > 10) {
            cy.log(`🎯 관련 select 발견: id="${id}", name="${name}", options=${optionsCount}, visible=${visible}`);
            
            // 옵션들 확인
            if (optionsCount > 0) {
              const options = [];
              for (let i = 0; i < Math.min(5, optionsCount); i++) {
                options.push(select.options[i].text);
              }
              cy.log(`  첫 옵션들: ${options.join(', ')}`);
            }
          }
        });
      });
    };
    
    // 5초마다 체크하면서 최대 10번 (50초) 반복
    for (let i = 0; i < 10; i++) {
      cy.wait(5000);
      cy.log(`🔄 ${(i + 1) * 5}초 경과 - 요소 상태 체크 중...`);
      checkForElements();
    }
    
    // 최종 스크린샷
    cy.screenshot('wait-for-elements-result');
    cy.log('🏁 대기 테스트 완료');
  });
});



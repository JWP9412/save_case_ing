describe('실제 캐차 입력 필드 찾기', function () {
  it('캐차 이미지 근처의 실제 입력 필드 찾기', function() {
    cy.visit('https://www.scourt.go.kr/portal/information/events/search/search.jsp');
    
    // 충분한 로딩 대기
    cy.wait(5000);
    
    // 캐차 이미지 먼저 찾기
    const captchaSelectors = [
      'img[src*="captcha"]',
      'img[src*="Captcha"]', 
      'img[src*=".on"]',
      'img[alt*="보안"]'
    ];
    
    captchaSelectors.forEach(selector => {
      cy.get('body').then($body => {
        if ($body.find(selector).length > 0) {
          cy.log(`캐차 이미지 발견: ${selector}`);
          
          cy.get(selector).first().then($img => {
            // 캐차 이미지의 부모, 형제, 다음 요소들 확인
            const imgElement = $img.get(0);
            
            cy.log('캐차 이미지 정보:');
            cy.log(`- src: ${imgElement.src}`);
            cy.log(`- id: ${imgElement.id || '없음'}`);
            cy.log(`- class: ${imgElement.className || '없음'}`);
            
            // 부모 요소 확인
            const parent = imgElement.parentElement;
            if (parent) {
              cy.log(`부모 요소: ${parent.tagName}, id: ${parent.id || '없음'}, class: ${parent.className || '없음'}`);
              
              // 부모 요소 내의 모든 input 찾기
              const inputs = parent.querySelectorAll('input');
              cy.log(`부모 내 input 개수: ${inputs.length}`);
              inputs.forEach((input, index) => {
                cy.log(`  Input ${index}: id="${input.id || '없음'}", name="${input.name || '없음'}", type="${input.type}", placeholder="${input.placeholder || '없음'}"`);
              });
            }
            
            // 캐차 이미지 다음 형제 요소들 확인
            let nextSibling = imgElement.nextElementSibling;
            let siblingCount = 0;
            while (nextSibling && siblingCount < 5) {
              cy.log(`다음 형제 ${siblingCount}: ${nextSibling.tagName}, id: ${nextSibling.id || '없음'}, class: ${nextSibling.className || '없음'}`);
              
              if (nextSibling.tagName === 'INPUT') {
                cy.log(`🎯 캐차 다음 input 발견! id: ${nextSibling.id}, name: ${nextSibling.name}, type: ${nextSibling.type}`);
              }
              
              // 자식 요소에서 input 찾기
              const childInputs = nextSibling.querySelectorAll('input');
              if (childInputs.length > 0) {
                cy.log(`형제 요소 내 input 발견: ${childInputs.length}개`);
                childInputs.forEach((input, index) => {
                  cy.log(`  🎯 Input ${index}: id="${input.id || '없음'}", name="${input.name || '없음'}", type="${input.type}"`);
                });
              }
              
              nextSibling = nextSibling.nextElementSibling;
              siblingCount++;
            }
          });
        }
      });
    });
    
    // 캐차 관련 텍스트 근처의 input도 찾기
    cy.contains('보안').then($element => {
      if ($element.length > 0) {
        cy.log('보안 텍스트 근처 input 찾기');
        const textElement = $element.get(0);
        const container = textElement.closest('div, form, section');
        if (container) {
          const inputs = container.querySelectorAll('input[type="text"], input[type="number"]');
          cy.log(`보안 텍스트 컨테이너 내 input: ${inputs.length}개`);
          inputs.forEach((input, index) => {
            cy.log(`  Input ${index}: id="${input.id || '없음'}", name="${input.name || '없음'}", visible: ${input.offsetParent !== null}`);
          });
        }
      }
    });
  });
});

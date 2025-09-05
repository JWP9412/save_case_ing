describe('캐차 요소 찾기', function () {
  it('새 사이트의 캐차 이미지 요소들 찾기', function() {
    cy.visit('https://www.scourt.go.kr/portal/information/events/search/search.jsp');
    
    // 충분한 로딩 대기 (WebSquare Framework)
    cy.wait(5000);
    
    // 모든 이미지 요소 확인
    cy.get('img').then($imgs => {
      console.log(`총 ${$imgs.length}개의 이미지 발견:`);
      $imgs.each((index, img) => {
        const id = img.id || '없음';
        const src = img.src || '없음';
        const className = img.className || '없음';
        const alt = img.alt || '없음';
        console.log(`Image ${index}: id="${id}", src="${src}", class="${className}", alt="${alt}"`);
        
        // 캐차로 의심되는 이미지 찾기
        if (src.includes('captcha') || src.includes('Captcha') || 
            src.includes('verify') || src.includes('security') ||
            id.includes('captcha') || id.includes('Captcha') ||
            className.includes('captcha') || className.includes('Captcha')) {
          console.log(`🎯 캐차 의심 이미지 발견! Image ${index}`);
        }
      });
    });
    
    // iframe 내부의 이미지도 확인
    cy.get('iframe').then($iframes => {
      if ($iframes.length > 0) {
        console.log(`${$iframes.length}개의 iframe 발견, 내부 확인 중...`);
        $iframes.each((index, iframe) => {
          const src = iframe.src || '없음';
          const id = iframe.id || '없음';
          console.log(`Iframe ${index}: id="${id}", src="${src}"`);
        });
      }
    });
    
    // 캐차 관련 텍스트 찾기
    const captchaTerms = ['보안', '인증', '자동', '방지', 'captcha', 'CAPTCHA', '문자', '숫자'];
    captchaTerms.forEach(term => {
      cy.get('body').then($body => {
        if ($body.text().includes(term)) {
          console.log(`"${term}" 텍스트 포함됨`);
          cy.contains(term).then($elements => {
            $elements.each((index, el) => {
              const tagName = el.tagName;
              const id = el.id || '없음';
              const className = el.className || '없음';
              console.log(`  - ${tagName}: id="${id}", class="${className}"`);
              
              // 주변 요소들도 확인
              const parent = el.parentElement;
              if (parent) {
                const parentId = parent.id || '없음';
                const parentClass = parent.className || '없음';
                console.log(`    부모: ${parent.tagName}, id="${parentId}", class="${parentClass}"`);
              }
            });
          });
        }
      });
    });
    
    // div 요소 중 캐차 관련된 것 찾기
    cy.get('div').then($divs => {
      console.log('캐차 관련 div 찾는 중...');
      $divs.each((index, div) => {
        const id = div.id || '';
        const className = div.className || '';
        
        if (id.toLowerCase().includes('captcha') || 
            className.toLowerCase().includes('captcha') ||
            id.toLowerCase().includes('verify') ||
            className.toLowerCase().includes('verify')) {
          console.log(`🎯 캐차 관련 div 발견! id="${id}", class="${className}"`);
        }
      });
    });
  });
});

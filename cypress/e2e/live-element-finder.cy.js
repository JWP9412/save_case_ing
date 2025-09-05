describe('실시간 요소 탐지', function () {
  it('새 사이트의 실제 사용 가능한 요소들 찾기', function() {
    cy.visit('https://www.scourt.go.kr/portal/information/events/search/search.jsp');
    
    // 충분한 로딩 대기
    cy.wait(8000);
    
    cy.log('🔍 새 사이트 실시간 분석 시작');
    
    // 1. 페이지 기본 정보
    cy.title().then(title => {
      cy.log(`📄 페이지 제목: ${title}`);
    });
    cy.url().should('include', 'scourt.go.kr');
    
    // 2. 모든 form 요소 찾기
    cy.get('form').then($forms => {
      cy.log(`📝 ${$forms.length}개의 form 발견`);
      $forms.each((index, form) => {
        const id = form.id || '없음';
        const action = form.action || '없음';
        const method = form.method || '없음';
        cy.log(`Form ${index}: id="${id}", action="${action}", method="${method}"`);
      });
    });
    
    // 3. 모든 input 찾기 (visible 조건 제거)
    cy.get('body').then($body => {
      const allInputs = $body.find('input');
      if (allInputs.length > 0) {
        cy.log(`📝 ${allInputs.length}개의 input 발견 (숨겨진 것 포함)`);
        allInputs.each((index, input) => {
          const id = input.id || '없음';
          const name = input.name || '없음';
          const type = input.type || '없음';
          const placeholder = input.placeholder || '없음';
          const visible = input.offsetParent !== null ? 'Y' : 'N';
          cy.log(`Input ${index}: id="${id}", name="${name}", type="${type}", placeholder="${placeholder}", visible=${visible}`);
        });
      } else {
        cy.log('❌ input 요소가 하나도 없음 - WebSquare 컴포넌트 또는 iframe 사용');
      }
    });
    
    // 4. 모든 select 찾기 (visible 조건 제거)
    cy.get('body').then($body => {
      const allSelects = $body.find('select');
      if (allSelects.length > 0) {
        cy.log(`📋 ${allSelects.length}개의 select 발견 (숨겨진 것 포함)`);
        allSelects.each((index, select) => {
          const id = select.id || '없음';
          const name = select.name || '없음';
          const optionsCount = select.options.length;
          const visible = select.offsetParent !== null ? 'Y' : 'N';
          cy.log(`Select ${index}: id="${id}", name="${name}", options=${optionsCount}, visible=${visible}`);
        });
      } else {
        cy.log('❌ select 요소가 하나도 없음 - WebSquare 컴포넌트 사용');
      }
    });
    
    // 5. 모든 clickable 요소 찾기 (visible 조건 제거)
    cy.get('body').then($body => {
      const allClickables = $body.find('button, input[type="submit"], input[type="button"], a[href]');
      if (allClickables.length > 0) {
        cy.log(`🖱️ ${allClickables.length}개의 클릭 가능한 요소 발견 (숨겨진 것 포함)`);
        allClickables.each((index, el) => {
          if (index < 10) { // 처음 10개만
            const id = el.id || '없음';
            const text = el.textContent?.trim() || el.value || '없음';
            const tagName = el.tagName;
            const onclick = el.onclick ? 'Y' : 'N';
            const visible = el.offsetParent !== null ? 'Y' : 'N';
            cy.log(`Click ${index}: ${tagName}, id="${id}", text="${text}", onclick=${onclick}, visible=${visible}`);
          }
        });
      } else {
        cy.log('❌ 클릭 가능한 요소가 하나도 없음');
      }
    });
    
    // 6. 특정 텍스트 포함 요소들 찾기
    const searchTexts = ['검색', '조회', '사건번호', '법원', '년도', '사건종류', '당사자'];
    searchTexts.forEach(text => {
      cy.get('body').then($body => {
        if ($body.text().includes(text)) {
          cy.contains(text).then($elements => {
            const element = $elements.first();
            if (element.length > 0) {
              const tagName = element.prop('tagName');
              const id = element.attr('id') || '없음';
              const className = element.attr('class') || '없음';
              cy.log(`"${text}" 근처: ${tagName}, id="${id}", class="${className}"`);
            }
          });
        }
      });
    });
    
    // 7. iframe 내부 확인
    cy.get('iframe').then($iframes => {
      if ($iframes.length > 0) {
        cy.log(`🖼️ ${$iframes.length}개의 iframe 발견`);
        $iframes.each((index, iframe) => {
          const src = iframe.src || '없음';
          const id = iframe.id || '없음';
          cy.log(`Iframe ${index}: id="${id}", src="${src}"`);
        });
      }
    });
    
    // 8. WebSquare 컴포넌트 확인
    cy.get('body').then($body => {
      // WebSquare 관련 모든 요소들 찾기
      const wsElements = $body.find('[id*="w2"], [class*="w2"], [data-*="w2"], [id*="websquare"], [class*="websquare"]');
      if (wsElements.length > 0) {
        cy.log(`⚡ ${wsElements.length}개의 WebSquare 컴포넌트 발견`);
        wsElements.each((index, ws) => {
          if (index < 10) { // 처음 10개만
            const id = ws.id || '없음';
            const className = ws.className || '없음';
            const tagName = ws.tagName;
            cy.log(`WS ${index}: ${tagName}, id="${id}", class="${className}"`);
          }
        });
      } else {
        cy.log('❌ WebSquare 컴포넌트 없음');
      }
      
      // 전체 페이지 HTML 구조 간단히 확인
      cy.log('📄 페이지 HTML 구조 (상위 요소들):');
      const topElements = $body.children();
      topElements.each((index, el) => {
        if (index < 5) { // 처음 5개만
          const id = el.id || '없음';
          const className = el.className || '없음';
          const tagName = el.tagName;
          const childrenCount = el.children.length;
          cy.log(`Top ${index}: ${tagName}, id="${id}", class="${className}", children=${childrenCount}`);
        }
      });
    });
    
    // 9. 실제 사용 가능한 검색 관련 요소들 체크
    cy.log('🎯 검색 관련 실제 사용 가능한 요소들:');
    
    // 법원 선택 관련
    const courtSelectors = ['select[name*="court"]', 'select[name*="bub"]', 'select[id*="court"]', 'select[id*="bub"]'];
    courtSelectors.forEach(selector => {
      cy.get('body').then($body => {
        if ($body.find(selector).length > 0) {
          cy.log(`✅ 법원 선택 가능: ${selector}`);
        }
      });
    });
    
    // 사건번호 입력 관련
    const caseSelectors = ['input[name*="case"]', 'input[name*="sa"]', 'input[id*="case"]', 'input[id*="sa"]'];
    caseSelectors.forEach(selector => {
      cy.get('body').then($body => {
        if ($body.find(selector).length > 0) {
          cy.log(`✅ 사건번호 입력 가능: ${selector}`);
        }
      });
    });
  });
});

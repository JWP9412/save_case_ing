const cases = require('../fixtures/cases_chunk_0.json');

describe('새로운 간편 사이트 테스트', function () {
  const [rowIndex, court, caseNumber, manager] = cases[0];
  
  it(`간편 사이트에서 사건검색: ${caseNumber}`, function() {
    cy.log(`🔍 처리할 사건: ${court} ${caseNumber} (${manager})`);
    
    // 사건번호에서 숫자만 추출
    const serialNumber = caseNumber.match(/[0-9]+$/)[0];
    cy.log(`📝 사건번호: ${serialNumber}, 당사자: ${manager}`);
    
    // 새로운 간편 사이트 접속
    cy.visit('https://ssgo.scourt.go.kr/ssgo/index.on?cortId=www');
    cy.wait(10000);
    cy.log('✅ 간편 사이트 접속 완료');
    
    // 페이지 구조 분석
    cy.log('🔍 페이지 구조 분석 중...');
    cy.get('body').then($body => {
      
      // 모든 input 요소 확인
      const allInputs = $body.find('input');
      cy.log(`📝 총 ${allInputs.length}개 input 요소 발견:`);
      
      allInputs.each((index, input) => {
        const id = input.id || '없음';
        const name = input.name || '없음';
        const type = input.type || '없음';
        const placeholder = input.placeholder || '없음';
        const maxLength = input.maxLength || '없음';
        const visible = input.offsetParent !== null;
        
        cy.log(`Input ${index}: type="${type}", id="${id}", name="${name}", placeholder="${placeholder}", maxLength=${maxLength}, visible=${visible}`);
      });
      
      // 모든 select 요소 확인
      const allSelects = $body.find('select');
      cy.log(`📋 총 ${allSelects.length}개 select 요소 발견:`);
      
      allSelects.each((index, select) => {
        const id = select.id || '없음';
        const name = select.name || '없음';
        const optionsCount = select.options.length;
        const visible = select.offsetParent !== null;
        
        cy.log(`Select ${index}: id="${id}", name="${name}", options=${optionsCount}, visible=${visible}`);
        
        // 옵션들도 확인 (처음 5개만)
        if (optionsCount > 0) {
          const options = [];
          for (let i = 0; i < Math.min(5, optionsCount); i++) {
            options.push(select.options[i].text);
          }
          cy.log(`  첫 옵션들: ${options.join(', ')}`);
        }
      });
      
      // 모든 button 요소 확인
      const allButtons = $body.find('button, input[type="submit"], input[type="button"]');
      cy.log(`🔘 총 ${allButtons.length}개 button 요소 발견:`);
      
      allButtons.each((index, button) => {
        const id = button.id || '없음';
        const value = button.value || button.textContent || '없음';
        const type = button.type || '없음';
        const visible = button.offsetParent !== null;
        
        cy.log(`Button ${index}: type="${type}", id="${id}", value/text="${value}", visible=${visible}`);
      });
      
      // 특정 키워드들이 있는지 확인
      const keywords = ['사건번호', '당사자', '법원', '검색', '조회', '사건검색'];
      keywords.forEach(keyword => {
        if ($body.text().includes(keyword)) {
          cy.log(`✅ "${keyword}" 텍스트 발견됨`);
        }
      });
    });
    
    // 실제 자동입력 시도
    cy.log('🎯 자동입력 시도 시작...');
    
    // 1. 사건번호입력모드 체크박스 체크
    cy.log('🎯 사건번호입력모드 체크박스 체크');
    const checkboxSelectors = [
      '#mf_ssgoTopMainTab_contents_content1_body_cbx_chkSanoInputMode_input_0',
      'input[title="사건번호입력모드"]',
      'input[name*="chkSanoInputMode"]'
    ];
    
    let checkboxFound = false;
    checkboxSelectors.forEach(selector => {
      cy.get('body').then($body => {
        if (!checkboxFound && $body.find(selector).length > 0) {
          cy.log(`☑️ 사건번호입력모드 체크박스 발견: ${selector}`);
          cy.get(selector).check({ force: true });
          cy.log('✅ 사건번호입력모드 체크 완료');
          checkboxFound = true;
        }
      });
    });
    
    cy.wait(1000);
    
    // 2. 사건번호 입력 시도
    cy.get('body').then($body => {
      const textInputs = $body.find('input[type="text"]:visible');
      if (textInputs.length > 0) {
        cy.log(`📝 보이는 텍스트 입력 필드 ${textInputs.length}개 발견`);
        
        // 첫 번째 텍스트 입력에 사건번호
        cy.get('input[type="text"]:visible').first().then($input => {
          cy.wrap($input).clear({ force: true });
          cy.wrap($input).type(serialNumber, { force: true });
          cy.log(`✅ 첫 번째 입력에 사건번호 입력: ${serialNumber}`);
        });
        
        // 두 번째 텍스트 입력에 당사자명 (있다면)
        if (textInputs.length > 1) {
          cy.get('input[type="text"]:visible').eq(1).then($input => {
            cy.wrap($input).clear({ force: true });
            cy.wrap($input).type(manager, { force: true });
            cy.log(`✅ 두 번째 입력에 당사자명 입력: ${manager}`);
          });
        }
      }
    });
    
    cy.wait(1000);
    
    // 3. 법원 선택 시도
    cy.get('body').then($body => {
      const selects = $body.find('select:visible');
      if (selects.length > 0) {
        cy.log(`📋 보이는 select ${selects.length}개 발견`);
        
        selects.each((index, select) => {
          const options = [];
          for (let i = 0; i < select.options.length; i++) {
            options.push(select.options[i].text);
          }
          
          // 서울중앙지방법원이 있는지 확인
          const seoulIndex = options.findIndex(opt => opt.includes('서울중앙'));
          if (seoulIndex >= 0) {
            cy.log(`🏛️ 서울중앙지방법원 발견, 선택 시도`);
            cy.get(select).select(seoulIndex, { force: true });
          }
        });
      }
    });
    
    cy.wait(2000);
    
    // 4. 검색 버튼 클릭
    cy.get('body').then($body => {
      const searchButtons = $body.find('button:visible, input[type="submit"]:visible, input[type="button"]:visible');
      if (searchButtons.length > 0) {
        cy.log(`🔍 보이는 버튼 ${searchButtons.length}개 발견, 첫 번째 클릭`);
        cy.get('button:visible, input[type="submit"]:visible, input[type="button"]:visible').first().click({ force: true });
        cy.log('✅ 검색 버튼 클릭 완료');
      }
    });
    
    // 결과 대기 및 스크린샷
    cy.wait(5000);
    cy.screenshot('new-site-test-result');
    cy.log('🎯 새로운 간편 사이트 테스트 완료');
  });
});

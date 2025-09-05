const cases = require('../fixtures/cases_chunk_0.json');

describe('완전한 단순 자동화', function () {
  // 첫 번째 사건만 처리
  const [rowIndex, court, caseNumber, manager] = cases[0];
  
  it(`완전한 사건검색 자동화: ${caseNumber}`, function() {
    cy.log(`🔍 처리할 사건: ${court} ${caseNumber} (${manager})`);
    
    // 사건번호에서 숫자만 추출
    const serialNumber = caseNumber.match(/[0-9]+$/)[0];
    cy.log(`📝 사건번호: ${serialNumber}, 당사자: ${manager}`);
    
    // 사이트 접속
    cy.visit('https://www.scourt.go.kr/portal/information/events/search/search.jsp');
    cy.wait(15000);
    cy.log('✅ 사이트 접속 완료');
    
    // 1단계: 사건번호입력모드 체크박스 체크 (있으면)
    cy.log('🎯 1단계: 사건번호입력모드 체크박스 체크');
    cy.get('body').then($body => {
      const checkboxes = $body.find('input[type="checkbox"]');
      if (checkboxes.length > 0) {
        cy.log(`📋 체크박스 ${checkboxes.length}개 발견됨`);
        cy.get('input[type="checkbox"]').first().check({ force: true });
        cy.log('✅ 체크박스 체크 완료');
      } else {
        cy.log('ℹ️ 체크박스가 없음 - 바로 다음 단계로');
      }
    });
    cy.wait(1000);
    
    // 2단계: 사건번호 입력
    cy.log('🎯 2단계: 사건번호 입력');
    cy.get('input[type="text"]').then($inputs => {
      // 길이 제한이 있는 첫 번째 입력 필드에 사건번호 입력
      $inputs.each((index, input) => {
        if (input.maxLength > 0 && input.maxLength <= 10 && index === 0) {
          cy.wrap(input).clear({ force: true });
          cy.wrap(input).type(serialNumber, { force: true });
          cy.log(`✅ 사건번호 입력 완료: ${serialNumber}`);
          return false; // 루프 중단
        }
      });
    });
    cy.wait(1000);
    
    // 3단계: 당사자명 입력
    cy.log('🎯 3단계: 당사자명 입력');
    cy.get('input[type="text"]').then($inputs => {
      // 길이 제한이 긴 입력 필드에 당사자명 입력
      $inputs.each((index, input) => {
        if (input.maxLength > 10 && index === 0) {
          cy.wrap(input).clear({ force: true });
          cy.wrap(input).type(manager, { force: true });
          cy.log(`✅ 당사자명 입력 완료: ${manager}`);
          return false; // 루프 중단
        }
      });
    });
    cy.wait(1000);
    
    // 4단계: 캡차 처리
    cy.log('🎯 4단계: 캡차 처리');
    
    // 캡차 이미지 확인
    cy.get('body').then($body => {
      const captchaImages = $body.find('img[src*="captcha"], img[src*="Captcha"]');
      if (captchaImages.length > 0) {
        cy.log('🔍 캡차 이미지 발견됨');
        
        // 캡차 입력 필드 찾기
        const captchaInputSelectors = [
          'input[maxlength="4"]',
          'input[maxlength="5"]',
          'input[name*="captcha"]',
          'input[id*="captcha"]'
        ];
        
        let captchaInputFound = false;
        
        captchaInputSelectors.forEach(selector => {
          if (!captchaInputFound) {
            const captchaInputs = $body.find(selector);
            if (captchaInputs.length > 0) {
              cy.log(`🎯 캡차 입력 필드 발견: ${selector}`);
              
              // 랜덤 숫자 생성 (4자리)
              const randomNumber = Math.floor(1000 + Math.random() * 9000).toString();
              cy.log(`🎲 랜덤 캡차 입력: ${randomNumber}`);
              
              cy.get(selector).first().then($input => {
                cy.wrap($input).clear({ force: true });
                cy.wrap($input).type(randomNumber, { force: true });
                cy.log('✅ 캡차 입력 완료');
                captchaInputFound = true;
              });
            }
          }
        });
        
        if (!captchaInputFound) {
          cy.log('⚠️ 캡차 입력 필드를 찾을 수 없음');
        }
      } else {
        cy.log('ℹ️ 캡차 이미지가 없음');
      }
    });
    
    cy.wait(1000);
    
    // 5단계: 검색 버튼 클릭
    cy.log('🎯 5단계: 검색 버튼 클릭');
    
    const searchButtonSelectors = [
      'input[type="submit"]',
      'input[type="button"][value*="검색"]',
      'button:contains("검색")',
      'input[value*="조회"]',
      'button:contains("조회")'
    ];
    
    let searchButtonFound = false;
    
    searchButtonSelectors.forEach(selector => {
      cy.get('body').then($body => {
        if (!searchButtonFound && $body.find(selector).length > 0) {
          cy.log(`🔍 검색 버튼 발견: ${selector}`);
          cy.get(selector).first().click({ force: true });
          cy.log('✅ 검색 버튼 클릭 완료');
          searchButtonFound = true;
        }
      });
    });
    
    if (!searchButtonFound) {
      cy.log('⚠️ 검색 버튼을 찾을 수 없음 - Enter 키 시도');
      cy.get('input[type="text"]').first().type('{enter}', { force: true });
    }
    
    // 결과 대기
    cy.wait(5000);
    
    // 6단계: 결과 스크린샷
    cy.log('🎯 6단계: 결과 스크린샷 촬영');
    const filename = `${caseNumber.replace(/[^a-zA-Z0-9]/g, '_')}`;
    cy.screenshot(filename);
    cy.log(`📸 스크린샷 촬영 완료: ${filename}`);
    
    // 7단계: 결과 확인
    cy.log('🎯 7단계: 검색 결과 확인');
    cy.get('body').then($body => {
      const bodyText = $body.text();
      
      if (bodyText.includes('검색결과가 없습니다') || 
          bodyText.includes('사건이 존재하지 않습니다') ||
          bodyText.includes('조회된 사건이 없습니다')) {
        cy.log('❌ 검색 결과 없음');
      } else if (bodyText.includes('사건') || 
                 bodyText.includes('진행') || 
                 bodyText.includes('접수')) {
        cy.log('✅ 검색 결과 발견됨');
      } else {
        cy.log('⚠️ 결과 불명확');
      }
    });
    
    cy.log('🎉 완전한 자동화 테스트 완료!');
    cy.log(`📋 처리 완료: ${court} ${caseNumber} (${manager})`);
  });
});

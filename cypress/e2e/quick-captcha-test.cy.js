const cases = require('../fixtures/cases_chunk_0.json');

describe('빠른 캡차 테스트', function () {
  const [rowIndex, court, caseNumber, manager] = cases[0];
  
  it(`빠른 캡차 테스트: ${caseNumber}`, function() {
    cy.log(`🔍 처리할 사건: ${court} ${caseNumber} (${manager})`);
    
    // 간편 사이트 접속
    cy.visit('https://ssgo.scourt.go.kr/ssgo/index.on?cortId=www');
    cy.wait(15000);
    cy.log('✅ 사이트 접속 완료');
    
    // 1단계: 법원 선택
    cy.log('🎯 1단계: 법원 선택 - 서울중앙지방법원');
    cy.get('body').then($body => {
      const selects = $body.find('select');
      selects.each((index, select) => {
        const options = [];
        for (let i = 0; i < select.options.length; i++) {
          options.push(select.options[i].text);
        }
        const seoulIndex = options.findIndex(opt => opt.includes('서울중앙'));
        if (seoulIndex >= 0) {
          cy.log(`✅ 서울중앙지방법원 발견! 인덱스: ${seoulIndex}`);
          cy.get(select).select(seoulIndex, { force: true });
          cy.log('✅ 서울중앙지방법원 선택 완료');
          return false;
        }
      });
    });
    
    cy.wait(2000);
    
    // 2단계: 체크박스 체크
    cy.log('🎯 2단계: 사건번호입력모드 체크박스 체크');
    cy.get('#mf_ssgoTopMainTab_contents_content1_body_cbx_chkSanoInputMode_input_0').check({ force: true });
    cy.log('✅ 체크박스 체크 완료');
    cy.wait(2000);
    
    // 3단계: 사건번호 입력
    cy.log('🎯 3단계: 사건번호 입력');
    cy.get('input[type="text"]:visible').first().then($input => {
      cy.wrap($input).clear({ force: true });
      cy.wrap($input).type(caseNumber, { force: true, delay: 50 });
      cy.log(`📝 사건번호 입력: "${caseNumber}"`);
    });
    
    cy.wait(1000);
    
    // 4단계: 당사자명 입력
    cy.log('🎯 4단계: 당사자명 입력');
    cy.get('body').then($body => {
      const visibleInputs = $body.find('input[type="text"]:visible');
      if (visibleInputs.length > 1) {
        cy.get('input[type="text"]:visible').eq(1).then($input => {
          cy.wrap($input).clear({ force: true });
          cy.wrap($input).type(manager, { force: true, delay: 50 });
          cy.log(`📝 당사자명 입력: "${manager}"`);
        });
      }
    });
    
    cy.wait(1000);
    
    // 5단계: 캡차 이미지 캡처 (빠른 버전)
    cy.log('🎯 5단계: 캡차 이미지 캡처');
    cy.get('body').then($body => {
      const captchaImage = $body.find('#mf_ssgoTopMainTab_contents_content1_body_img_captcha');
      if (captchaImage.length > 0) {
        cy.log('🔍 6글자 캡차 이미지 발견됨');
        
        // 캡차 이미지 정보 로깅
        const img = captchaImage[0];
        cy.log(`📸 캡차 이미지 정보:`);
        cy.log(`  - src: ${img.src}`);
        cy.log(`  - alt: ${img.alt || '없음'}`);
        cy.log(`  - title: ${img.title || '없음'}`);
        cy.log(`  - 크기: ${img.width || '없음'}x${img.height || '없음'}`);
        
        // 캡차 이미지 스크린샷 촬영
        cy.log('📸 캡차 이미지 스크린샷 촬영');
        cy.screenshot('quick-captcha-image');
        
        // 사용자에게 안내 메시지
        cy.log('👤 사용자 안내:');
        cy.log('📋 위의 스크린샷에서 6글자 캡차를 확인하세요');
        cy.log('💡 실제 사용 시에는 팝업에서 입력하거나 콘솔에서 입력합니다');
        
        // 테스트용 랜덤 6글자 생성
        const testCaptcha = Math.random().toString(36).substring(2, 8).toUpperCase();
        cy.log(`🎲 테스트용 랜덤 6글자: "${testCaptcha}"`);
        
        // 캡차 입력 필드에 입력
        cy.get('#mf_ssgoTopMainTab_contents_content1_body_ibx_answer').then($input => {
          cy.log('📝 테스트 캡차 입력 중...');
          cy.wrap($input).clear({ force: true });
          cy.wait(500);
          
          // 한 글자씩 입력
          const chars = testCaptcha.split('');
          chars.forEach((char, index) => {
            cy.wrap($input).type(char, { force: true, delay: 100 });
            cy.log(`🔤 캡차 글자 ${index + 1}/${chars.length}: "${char}" 입력`);
          });
          
          cy.wait(1000);
          cy.wrap($input).then($updated => {
            const inputValue = $updated.val();
            cy.log(`✅ 테스트 캡차 입력 완료: "${inputValue}"`);
          });
        });
        
        // 캡차 입력 후 스크린샷
        cy.log('📸 캡차 입력 후 스크린샷');
        cy.screenshot('quick-captcha-after-input');
        
      } else {
        cy.log('ℹ️ 캡차 이미지가 없음');
      }
    });
    
    cy.wait(2000);
    
    // 6단계: 검색 버튼 클릭
    cy.log('🎯 6단계: 검색 버튼 클릭');
    const searchButtonSelectors = [
      'input[type="submit"]',
      'input[type="button"][value*="검색"]',
      'input[type="button"][value*="조회"]',
      'button:contains("검색")',
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
      cy.get('input[type="text"]:visible').first().type('{enter}', { force: true });
    }
    
    // 결과 대기
    cy.wait(3000);
    
    // 7단계: 최종 결과 스크린샷
    cy.log('🎯 7단계: 최종 결과 스크린샷');
    cy.screenshot('quick-captcha-final-result');
    
    // 8단계: 결과 확인
    cy.log('🎯 8단계: 빠른 캡차 테스트 결과 확인');
    cy.get('body').then($body => {
      const bodyText = $body.text();
      
      if (bodyText.includes('자동입력방지') || bodyText.includes('보안문자') || bodyText.includes('잘못')) {
        cy.log('❌ 캡차 실패 감지됨 (예상됨 - 랜덤 입력)');
        cy.log('💡 실제 사용 시에는 정확한 캡차를 입력하세요');
      } else if (bodyText.includes('검색결과') || bodyText.includes('사건정보')) {
        cy.log('✅ 캡차 성공! 검색 완료!');
      } else {
        cy.log('ℹ️ 캡차 결과 불명확');
      }
    });
    
    cy.log('🎉 빠른 캡차 테스트 완료!');
    cy.log('📸 생성된 스크린샷에서 캡차 이미지를 확인할 수 있습니다');
  });
});


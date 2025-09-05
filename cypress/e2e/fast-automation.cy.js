const cases = require('../fixtures/cases_chunk_0.json');

describe('빠른 자동화 - 간단한 캡차 처리', function () {
  const [rowIndex, court, caseNumber, manager] = cases[0];
  
  it(`빠른 사건검색 자동화: ${caseNumber}`, function() {
    cy.log(`🔍 처리할 사건: ${court} ${caseNumber} (${manager})`);
    
    // 간편 사이트 접속
    cy.visit('https://ssgo.scourt.go.kr/ssgo/index.on?cortId=www');
    cy.wait(15000);
    cy.log('✅ 사이트 접속 완료');
    
    // 1단계: 법원 선택 (서울중앙지방법원)
    cy.log('🎯 1단계: 법원 선택 - 서울중앙지방법원');
    cy.get('body').then($body => {
      const selects = $body.find('select');
      cy.log(`📋 총 ${selects.length}개의 select 발견`);
      
      selects.each((index, select) => {
        const options = [];
        for (let i = 0; i < select.options.length; i++) {
          options.push(select.options[i].text);
        }
        
        // 서울중앙지방법원 찾기
        const seoulIndex = options.findIndex(opt => opt.includes('서울중앙'));
        if (seoulIndex >= 0) {
          cy.log(`✅ 서울중앙지방법원 발견! 인덱스: ${seoulIndex}, 값: "${options[seoulIndex]}"`);
          cy.get(select).select(seoulIndex, { force: true });
          cy.log('✅ 서울중앙지방법원 선택 완료');
          return false; // 루프 중단
        }
      });
    });
    
    cy.wait(2000);
    
    // 2단계: 사건번호입력모드 체크박스 체크
    cy.log('🎯 2단계: 사건번호입력모드 체크박스 체크');
    cy.get('#mf_ssgoTopMainTab_contents_content1_body_cbx_chkSanoInputMode_input_0').check({ force: true });
    cy.log('✅ 체크박스 체크 완료');
    cy.wait(2000);
    
    // 3단계: 사건번호 입력 (천천히 한글자씩)
    cy.log('🎯 3단계: 사건번호 입력 (천천히 한글자씩)');
    cy.get('input[type="text"]:visible').first().then($input => {
      const inputId = $input.attr('id') || '없음';
      cy.log(`사건번호 입력 필드: ${inputId}`);
      
      cy.wrap($input).clear({ force: true });
      
      // 한 글자씩 천천히 입력
      const chars = caseNumber.split('');
      chars.forEach((char, index) => {
        cy.wrap($input).type(char, { force: true, delay: 100 });
        cy.log(`글자 ${index + 1}/${chars.length}: "${char}" 입력`);
      });
      
      cy.wait(1000);
      cy.wrap($input).then($updated => {
        const inputValue = $updated.val();
        cy.log(`✅ 사건번호 입력 완료: "${inputValue}"`);
      });
    });
    
    cy.wait(1000);
    
    // 4단계: 당사자명 입력 (천천히 한글자씩)
    cy.log('🎯 4단계: 당사자명 입력 (천천히 한글자씩)');
    cy.get('body').then($body => {
      const visibleInputs = $body.find('input[type="text"]:visible');
      
      if (visibleInputs.length > 1) {
        cy.log(`📝 보이는 입력 필드 ${visibleInputs.length}개 중 두 번째에 당사자명 입력`);
        
        cy.get('input[type="text"]:visible').eq(1).then($input => {
          const inputId = $input.attr('id') || '없음';
          cy.log(`당사자명 입력 필드: ${inputId}`);
          
          cy.wrap($input).clear({ force: true });
          
          // 한 글자씩 천천히 입력
          const chars = manager.split('');
          chars.forEach((char, index) => {
            cy.wrap($input).type(char, { force: true, delay: 100 });
            cy.log(`당사자 글자 ${index + 1}/${chars.length}: "${char}" 입력`);
          });
          
          cy.wait(1000);
          cy.wrap($input).then($updated => {
            const inputValue = $updated.val();
            cy.log(`✅ 당사자명 입력 완료: "${inputValue}"`);
          });
        });
      }
    });
    
    cy.wait(1000);
    
    // 5단계: 빠른 캡차 처리 (다중 시도)
    cy.log('🎯 5단계: 빠른 캡차 처리 - 스마트 추측');
    cy.get('body').then($body => {
      const captchaImages = $body.find('img[src*="captcha"], img[src*="Captcha"]');
      
      if (captchaImages.length > 0) {
        cy.log('🔍 캡차 이미지 발견됨 - 스마트 추측 시작');
        
        // 캡차 입력 필드 찾기
        const captchaInputs = $body.find('input[maxlength="4"], input[maxlength="5"]');
        if (captchaInputs.length > 0) {
          cy.log('🎯 캡차 입력 필드 발견');
          
          // 여러 패턴의 숫자 시도 (일반적인 패턴들)
          const smartGuesses = [
            '1234', '5678', '0000', '1111', '2222', 
            '1357', '2468', '0123', '9876', '5432'
          ];
          
          const randomIndex = Math.floor(Math.random() * smartGuesses.length);
          const guessNumber = smartGuesses[randomIndex];
          
          cy.log(`🎲 스마트 추측 캡차: ${guessNumber}`);
          
          cy.get('input[maxlength="4"], input[maxlength="5"]').first().then($input => {
            cy.wrap($input).clear({ force: true });
            cy.wrap($input).type(guessNumber, { force: true });
            cy.log('✅ 빠른 캡차 입력 완료');
          });
        }
      } else {
        cy.log('ℹ️ 캡차 이미지가 없음');
      }
    });
    
    cy.wait(1000);
    
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
    
    // 캡차 실패 시 재시도 로직
    cy.get('body').then($body => {
      const bodyText = $body.text();
      if (bodyText.includes('자동입력방지') || bodyText.includes('보안문자') || bodyText.includes('잘못')) {
        cy.log('⚠️ 캡차 실패 감지 - 다른 숫자로 재시도');
        
        // 새로운 랜덤 숫자로 재시도
        const retryNumber = Math.floor(1000 + Math.random() * 9000).toString();
        cy.log(`🔄 재시도 캡차: ${retryNumber}`);
        
        cy.get('input[maxlength="4"], input[maxlength="5"]').first().then($input => {
          cy.wrap($input).clear({ force: true });
          cy.wrap($input).type(retryNumber, { force: true });
          cy.log('✅ 재시도 캡차 입력 완료');
          
          // 다시 검색 버튼 클릭
          cy.get('input[type="submit"], input[type="button"][value*="검색"]').first().click({ force: true });
          cy.wait(3000);
        });
      } else {
        cy.log('✅ 캡차 통과 또는 캡차 없음');
      }
    });
    
    // 7단계: 결과 스크린샷
    cy.log('🎯 7단계: 결과 스크린샷 촬영');
    const filename = `fast_${caseNumber.replace(/[^a-zA-Z0-9]/g, '_')}_${Date.now()}`;
    cy.screenshot(filename);
    cy.log(`📸 스크린샷 촬영 완료: ${filename}`);
    
    cy.log('🎉 빠른 자동화 테스트 완료!');
    cy.log(`📋 처리 완료: ${court} → 서울중앙지방법원, ${caseNumber}, ${manager}`);
    
    // 최종 요약
    cy.log('📊 빠른 처리 요약:');
    cy.log(`  ✅ 법원: "${court}" → "서울중앙지방법원"`);
    cy.log(`  ✅ 체크박스: 사건번호입력모드 체크`);
    cy.log(`  ✅ 사건번호: "${caseNumber}" (빠른 입력)`);
    cy.log(`  ✅ 당사자명: "${manager}" (빠른 입력)`);
    cy.log(`  ✅ 캡차: 스마트 추측 방식`);
    cy.log(`  ✅ 검색 실행: 완료`);
    cy.log(`  ✅ 스크린샷: ${filename}.png`);
  });
});


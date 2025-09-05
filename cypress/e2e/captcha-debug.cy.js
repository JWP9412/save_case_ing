const cases = require('../fixtures/cases_chunk_0.json');

describe('캡차 처리 디버그 - 자세한 로그', function () {
  const [rowIndex, court, caseNumber, manager] = cases[0];
  
  it(`캡차 처리 디버그: ${caseNumber}`, function() {
    cy.log(`🔍 처리할 사건: ${court} ${caseNumber} (${manager})`);
    
    // 간편 사이트 접속
    cy.visit('https://ssgo.scourt.go.kr/ssgo/index.on?cortId=www');
    cy.wait(15000);
    cy.log('✅ 사이트 접속 완료');
    
    // 1단계: 법원 선택
    cy.log('🎯 1단계: 법원 선택 - 서울중앙지방법원');
    cy.get('body').then($body => {
      const selects = $body.find('select');
      cy.log(`📋 총 ${selects.length}개의 select 발견`);
      
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
    
    // 5단계: 캡차 상세 분석 및 처리 (정확한 ID 사용)
    cy.log('🎯 5단계: 캡차 상세 분석 및 처리');
    cy.get('body').then($body => {
      // 정확한 캡차 이미지 찾기
      const captchaImage = $body.find('#mf_ssgoTopMainTab_contents_content1_body_img_captcha');
      cy.log(`🖼️ 캡차 이미지 발견: ${captchaImage.length}개`);
      
      if (captchaImage.length > 0) {
        const img = captchaImage[0];
        const src = img.src;
        const alt = img.alt || '없음';
        const title = img.title || '없음';
        const width = img.width || '없음';
        const height = img.height || '없음';
        cy.log(`📸 캡차 이미지: src="${src}", alt="${alt}", title="${title}", 크기=${width}x${height}`);
        
        // 정확한 캡차 입력 필드 찾기
        const captchaInput = $body.find('#mf_ssgoTopMainTab_contents_content1_body_ibx_answer');
        cy.log(`📝 캡차 입력 필드 발견: ${captchaInput.length}개`);
        
        if (captchaInput.length > 0) {
          const input = captchaInput[0];
          const id = input.id || '없음';
          const title = input.title || '없음';
          const placeholder = input.placeholder || '없음';
          const maxlength = input.maxLength || '없음';
          cy.log(`📝 캡차 입력 필드: id="${id}", title="${title}", placeholder="${placeholder}", maxlength="${maxlength}"`);
          
          // 캡차 이미지 스크린샷 촬영
          cy.log('📸 캡차 이미지 스크린샷 촬영');
          cy.screenshot('captcha-image-before');
          
          // 여러 패턴의 캡차 시도
          const captchaPatterns = [
            '1234', '5678', '0000', '1111', '9999', 
            '1357', '2468', '0123', '9876', '5432',
            'ABCD', 'EFGH', 'IJKL', 'MNOP', 'QRST'
          ];
          
          const selectedPattern = captchaPatterns[Math.floor(Math.random() * captchaPatterns.length)];
          cy.log(`🎲 선택된 캡차 패턴: "${selectedPattern}"`);
          
          // 정확한 캡차 입력 필드에 입력
          cy.get('#mf_ssgoTopMainTab_contents_content1_body_ibx_answer').then($input => {
            cy.log('📝 캡차 입력 시작');
            cy.wrap($input).clear({ force: true });
            cy.wait(500);
            
            // 한 글자씩 입력하여 로그 확인
            const chars = selectedPattern.split('');
            chars.forEach((char, index) => {
              cy.wrap($input).type(char, { force: true, delay: 200 });
              cy.log(`🔤 캡차 글자 ${index + 1}/${chars.length}: "${char}" 입력`);
              cy.wait(100);
            });
            
            cy.wait(1000);
            cy.wrap($input).then($updated => {
              const inputValue = $updated.val();
              cy.log(`✅ 캡차 입력 완료: "${inputValue}"`);
              
              if (inputValue === selectedPattern) {
                cy.log('✅ 캡차 정확히 입력됨!');
              } else {
                cy.log(`⚠️ 캡차 불일치: 예상 "${selectedPattern}", 실제 "${inputValue}"`);
              }
            });
          });
          
          // 캡차 입력 후 스크린샷
          cy.log('📸 캡차 입력 후 스크린샷 촬영');
          cy.screenshot('captcha-image-after');
          
        } else {
          cy.log('❌ 캡차 입력 필드 #mf_ssgoTopMainTab_contents_content1_body_ibx_answer를 찾을 수 없음');
        }
      } else {
        cy.log('ℹ️ 캡차 이미지 #mf_ssgoTopMainTab_contents_content1_body_img_captcha가 없음');
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
    
    // 결과 대기 및 확인
    cy.wait(5000);
    
    // 7단계: 최종 결과 스크린샷
    cy.log('🎯 7단계: 최종 결과 스크린샷');
    cy.screenshot('final-result');
    
    // 8단계: 페이지 상태 확인
    cy.log('🎯 8단계: 페이지 상태 확인');
    cy.get('body').then($body => {
      const bodyText = $body.text();
      
      // 에러 메시지 확인
      if (bodyText.includes('자동입력방지') || bodyText.includes('보안문자') || bodyText.includes('잘못')) {
        cy.log('❌ 캡차 실패 감지됨');
        cy.log('📝 페이지 내용에서 에러 메시지 발견');
      } else if (bodyText.includes('검색결과') || bodyText.includes('사건정보')) {
        cy.log('✅ 검색 성공!');
      } else {
        cy.log('ℹ️ 검색 결과 불명확');
      }
      
      // 입력 필드 상태 재확인
      const visibleInputs = $body.find('input[type="text"]:visible');
      cy.log(`📝 현재 보이는 입력 필드: ${visibleInputs.length}개`);
      
      visibleInputs.each((index, input) => {
        const id = input.id || '없음';
        const value = input.value || '비어있음';
        const placeholder = input.placeholder || '없음';
        cy.log(`📝 Input ${index + 1}: id="${id}", value="${value}", placeholder="${placeholder}"`);
      });
    });
    
    cy.log('🎉 캡차 디버그 테스트 완료!');
  });
});

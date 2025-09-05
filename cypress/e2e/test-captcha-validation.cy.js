const cases = require('../fixtures/cases_chunk_0.json');

describe('캡차 검증 테스트', function () {
  const [rowIndex, court, caseNumber, manager] = cases[0];
  
  it('캡차가 실제로 검증되는지 확인', function() {
    cy.log('🔍 캡차 검증 방식 분석 시작');
    
    // 간편 사이트 접속
    cy.visit('https://ssgo.scourt.go.kr/ssgo/index.on?cortId=www');
    cy.wait(15000);
    cy.log('✅ 사이트 접속 완료');
    
    // 기본 설정
    cy.log('🎯 기본 입력 완료');
    
    // 법원 선택
    cy.get('body').then($body => {
      const selects = $body.find('select');
      selects.each((index, select) => {
        const options = [];
        for (let i = 0; i < select.options.length; i++) {
          options.push(select.options[i].text);
        }
        const seoulIndex = options.findIndex(opt => opt.includes('서울중앙'));
        if (seoulIndex >= 0) {
          cy.get(select).select(seoulIndex, { force: true });
          return false;
        }
      });
    });
    
    // 체크박스
    cy.get('#mf_ssgoTopMainTab_contents_content1_body_cbx_chkSanoInputMode_input_0').check({ force: true });
    cy.wait(2000);
    
    // 사건번호
    cy.get('input[type="text"]:visible').first().then($input => {
      cy.wrap($input).clear({ force: true });
      const chars = caseNumber.split('');
      chars.forEach((char) => {
        cy.wrap($input).type(char, { force: true, delay: 100 });
      });
    });
    
    // 당사자명
    cy.get('input[type="text"]:visible').eq(1).then($input => {
      cy.wrap($input).clear({ force: true });
      const chars = manager.split('');
      chars.forEach((char) => {
        cy.wrap($input).type(char, { force: true, delay: 100 });
      });
    });
    
    cy.wait(1000);
    
    // 캡차 테스트 시작
    cy.log('🎯 캡차 검증 테스트 시작');
    
    // 테스트 1: 아무것도 입력하지 않고 검색
    cy.log('📝 테스트 1: 캡차 빈칸으로 검색');
    cy.get('input[type="submit"]').first().click({ force: true });
    cy.wait(3000);
    
    cy.get('body').then($body => {
      const bodyText = $body.text();
      cy.log(`결과 1: ${bodyText.includes('자동입력') ? '캡차 필수' : '캡차 검증 없음'}`);
    });
    
    cy.wait(2000);
    
    // 테스트 2: 틀린 숫자 입력
    cy.log('📝 테스트 2: 틀린 캡차로 검색');
    cy.get('body').then($body => {
      const captchaInputs = $body.find('input[maxlength="4"], input[maxlength="5"], input[maxlength="6"]');
      if (captchaInputs.length > 0) {
        cy.get('input[maxlength="4"], input[maxlength="5"], input[maxlength="6"]').first().then($input => {
          cy.wrap($input).clear({ force: true });
          cy.wrap($input).type('000000', { force: true }); // 의도적으로 틀린 값
          cy.log('틀린 캡차 입력: 000000');
        });
        
        cy.get('input[type="submit"]').first().click({ force: true });
        cy.wait(3000);
        
        cy.get('body').then($body2 => {
          const bodyText2 = $body2.text();
          cy.log(`결과 2: ${bodyText2.includes('틀렸') || bodyText2.includes('다시') ? '캡차 검증 있음' : '캡차 검증 없음'}`);
        });
      }
    });
    
    // 테스트 3: 캡차 이미지 URL 분석
    cy.log('📝 테스트 3: 캡차 이미지 분석');
    cy.get('body').then($body => {
      const captchaImages = $body.find('img[src*="captcha"], img[src*="Captcha"]');
      if (captchaImages.length > 0) {
        const captchaSrc = captchaImages.first().attr('src');
        cy.log(`캡차 이미지 URL: ${captchaSrc}`);
        
        // URL에서 패턴 찾기
        const urlNumbers = captchaSrc.match(/\d+/g);
        if (urlNumbers) {
          cy.log(`URL에서 발견된 숫자들: ${urlNumbers.join(', ')}`);
        }
        
        // 이미지 크기나 특성 확인
        cy.get('img[src*="captcha"], img[src*="Captcha"]').first().then($img => {
          const width = $img.width();
          const height = $img.height();
          cy.log(`캡차 이미지 크기: ${width}x${height}`);
        });
      } else {
        cy.log('❌ 캡차 이미지를 찾을 수 없음');
      }
    });
    
    // 테스트 4: 개발자 도구에서 캡차 관련 요소 확인
    cy.log('📝 테스트 4: 페이지 소스에서 캡차 관련 코드 확인');
    cy.get('body').then($body => {
      const htmlContent = $body.html();
      
      // 캡차 관련 키워드 검색
      const captchaKeywords = ['captcha', 'Captcha', 'CAPTCHA', '자동입력', '보안문자', 'security'];
      const foundKeywords = captchaKeywords.filter(keyword => 
        htmlContent.toLowerCase().includes(keyword.toLowerCase())
      );
      
      cy.log(`페이지에서 발견된 캡차 관련 키워드: ${foundKeywords.join(', ')}`);
      
      // JavaScript 함수 확인
      if (htmlContent.includes('function') && htmlContent.includes('captcha')) {
        cy.log('✅ 캡차 관련 JavaScript 함수 발견됨');
      }
    });
    
    // 최종 스크린샷
    cy.screenshot('captcha_validation_test');
    cy.log('📸 캡차 검증 테스트 완료');
  });
});



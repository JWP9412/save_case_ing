const cases = require('../fixtures/cases_chunk_0.json');

describe('OCR 캐차 완전 자동화', function () {
  const [rowIndex, court, caseNumber, manager] = cases[0];
  
  it(`OCR 캡차 완전 자동 사건검색: ${caseNumber}`, function() {
    cy.log(`🚀 OCR 완전 자동화 시작: ${court} ${caseNumber} (${manager})`);
    
    // Tesseract.js 로드
    cy.window().then((win) => {
      return new Promise((resolve) => {
        const script = win.document.createElement('script');
        script.src = 'https://unpkg.com/tesseract.js@4/dist/tesseract.min.js';
        script.onload = () => {
          cy.log('✅ Tesseract.js 로드 완료');
          resolve();
        };
        win.document.head.appendChild(script);
      });
    });
    
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
          cy.log(`✅ 서울중앙지방법원 발견! 인덱스: ${seoulIndex}`);
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
    
    // 5단계: OCR 캡차 처리 🤖
    cy.log('🎯 5단계: OCR을 이용한 캡차 자동 인식');
    
    // 최대 5번 시도
    const maxAttempts = 5;
    let currentAttempt = 0;
    
    function attemptCaptcha() {
      currentAttempt++;
      cy.log(`🔄 캡차 시도 ${currentAttempt}/${maxAttempts}`);
      
      cy.get('body').then($body => {
        const captchaImages = $body.find('img[src*="captcha"], img[src*="Captcha"], img[alt*="보안"], img[alt*="자동입력"]');
        
        if (captchaImages.length > 0) {
          const captchaImg = captchaImages.first();
          const captchaSrc = captchaImg.attr('src');
          cy.log(`🔍 캡차 이미지 발견: ${captchaSrc}`);
          
          // OCR 처리
          cy.window().then((win) => {
            return new Promise((resolve) => {
              const img = new win.Image();
              img.crossOrigin = 'anonymous';
              img.onload = function() {
                // Canvas에 이미지 그리기
                const canvas = win.document.createElement('canvas');
                const ctx = canvas.getContext('2d');
                canvas.width = img.width;
                canvas.height = img.height;
                ctx.drawImage(img, 0, 0);
                
                // Tesseract로 OCR 수행
                win.Tesseract.recognize(canvas, 'eng', {
                  logger: m => {
                    if (m.status === 'recognizing text') {
                      cy.log(`🤖 OCR 진행률: ${Math.round(m.progress * 100)}%`);
                    }
                  }
                }).then(({ data: { text } }) => {
                  const captchaResult = text.replace(/[^0-9]/g, ''); // 숫자만 추출
                  cy.log(`🤖 OCR 인식 결과: "${captchaResult}"`);
                  
                  if (captchaResult.length >= 4) {
                    const captchaValue = captchaResult.slice(0, 6); // 최대 6자리
                    cy.log(`✅ 캡차 값 추출: ${captchaValue}`);
                    
                    // 캡차 입력
                    const captchaInputs = $body.find('input[maxlength="4"], input[maxlength="5"], input[maxlength="6"]');
                    if (captchaInputs.length > 0) {
                      cy.get('input[maxlength="4"], input[maxlength="5"], input[maxlength="6"]').first().then($input => {
                        cy.wrap($input).clear({ force: true });
                        cy.wrap($input).type(captchaValue, { force: true });
                        cy.log(`✅ 캡차 입력 완료: ${captchaValue}`);
                        resolve(captchaValue);
                      });
                    } else {
                      cy.log('❌ 캡차 입력 필드를 찾을 수 없음');
                      resolve(null);
                    }
                  } else {
                    cy.log(`❌ OCR 인식 실패: 숫자가 부족함 (${captchaResult.length}자리)`);
                    resolve(null);
                  }
                }).catch(err => {
                  cy.log(`❌ OCR 오류: ${err.message}`);
                  resolve(null);
                });
              };
              
              img.onerror = () => {
                cy.log('❌ 캡차 이미지 로드 실패');
                resolve(null);
              };
              
              // 절대 URL로 변환
              if (captchaSrc.startsWith('/')) {
                img.src = `https://ssgo.scourt.go.kr${captchaSrc}`;
              } else {
                img.src = captchaSrc;
              }
            });
          }).then((result) => {
            if (result) {
              // 검색 시도
              cy.log('🔍 검색 버튼 클릭 시도');
              
              const searchSelectors = [
                'input[type="submit"]',
                'button[type="submit"]',
                'input[value*="검색"]',
                'input[value*="조회"]',
                'button:contains("검색")',
                'button:contains("조회")'
              ];
              
              let searchButtonFound = false;
              searchSelectors.forEach(selector => {
                cy.get('body').then($searchBody => {
                  if (!searchButtonFound && $searchBody.find(selector).length > 0) {
                    cy.log(`🔍 검색 버튼 발견: ${selector}`);
                    cy.get(selector).first().click({ force: true });
                    searchButtonFound = true;
                  }
                });
              });
              
              if (!searchButtonFound) {
                cy.log('⚠️ 검색 버튼 못 찾음 - Enter 키 시도');
                cy.get('input[type="text"]:visible').first().type('{enter}', { force: true });
              }
              
              // 결과 확인
              cy.wait(5000);
              cy.get('body').then($resultBody => {
                const resultText = $resultBody.text();
                
                if (resultText.includes('자동입력') || resultText.includes('캡차') || resultText.includes('다시')) {
                  cy.log(`❌ 캡차 실패 (시도 ${currentAttempt}/${maxAttempts})`);
                  
                  if (currentAttempt < maxAttempts) {
                    cy.log('🔄 캡차 재시도...');
                    cy.reload();
                    cy.wait(10000);
                    attemptCaptcha(); // 재귀 호출
                  } else {
                    cy.log('❌ 최대 시도 횟수 도달 - 수동 처리 필요');
                  }
                } else {
                  cy.log('🎉 캡차 성공! 검색 완료!');
                }
              });
            } else {
              cy.log(`❌ OCR 실패 (시도 ${currentAttempt}/${maxAttempts})`);
              
              if (currentAttempt < maxAttempts) {
                // 랜덤 숫자로 시도
                const randomCaptcha = Math.floor(100000 + Math.random() * 900000).toString();
                cy.log(`🎲 랜덤 캡차 시도: ${randomCaptcha}`);
                
                const captchaInputs = $body.find('input[maxlength="4"], input[maxlength="5"], input[maxlength="6"]');
                if (captchaInputs.length > 0) {
                  cy.get('input[maxlength="4"], input[maxlength="5"], input[maxlength="6"]').first().then($input => {
                    cy.wrap($input).clear({ force: true });
                    cy.wrap($input).type(randomCaptcha, { force: true });
                  });
                }
                
                cy.reload();
                cy.wait(10000);
                attemptCaptcha(); // 재귀 호출
              }
            }
          });
        } else {
          cy.log('ℹ️ 캡차 이미지가 없음 - 바로 검색 시도');
          cy.get('input[type="submit"]').first().click({ force: true });
        }
      });
    }
    
    // 캡차 시도 시작
    attemptCaptcha();
    
    // 최종 스크린샷
    cy.wait(3000);
    const filename = `ocr_complete_${caseNumber.replace(/[^a-zA-Z0-9]/g, '_')}_${Date.now()}`;
    cy.screenshot(filename);
    cy.log(`📸 OCR 완전 자동화 결과: ${filename}`);
    
    // 최종 요약
    cy.log('🏆 OCR 완전 자동화 요약:');
    cy.log(`  ✅ 법원: "${court}" → "서울중앙지방법원"`);
    cy.log(`  ✅ 사건번호: "${caseNumber}"`);
    cy.log(`  ✅ 당사자명: "${manager}"`);
    cy.log(`  🤖 캡차: OCR 자동 인식 (최대 ${maxAttempts}번 시도)`);
    cy.log(`  📸 스크린샷: ${filename}.png`);
    cy.log('🚀 OCR 완전 자동화 완료!');
  });
});



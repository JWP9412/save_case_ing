const cases = require('../fixtures/cases_chunk_0.json');

describe('실시간 대화형 캡차 자동화', function () {
  const [rowIndex, court, caseNumber, manager] = cases[0];
  
  it(`실시간 캡차 자동화: ${caseNumber}`, function() {
    cy.log(`🔍 처리할 사건: ${court} ${caseNumber} (${manager})`);
    
    // 간편 사이트 접속
    cy.visit('https://ssgo.scourt.go.kr/ssgo/index.on?cortId=www');
    cy.wait(5000);
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
    
    // 5단계: 실시간 캡차 처리
    cy.log('🎯 5단계: 실시간 캡차 처리');
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
        
        // 캡차 이미지만 따로 캡처
        cy.log('📸 캡차 이미지만 따로 캡처');
        cy.get('#mf_ssgoTopMainTab_contents_content1_body_img_captcha').screenshot('realtime-captcha-image');
        
        // 실시간 처리 표 표시 (브라우저 콘솔에 출력)
        cy.window().then((win) => {
          win.console.log('📋 ==========================================');
          win.console.log('📋 실시간 캡차 처리 표');
          win.console.log('📋 ==========================================');
          win.console.log('📋 | 사건 번호 | 캡차 이미지 | 사용자 입력 |');
          win.console.log('📋 |----------|-------------|-------------|');
          win.console.log(`📋 | ${caseNumber} | realtime-captcha-image.png | 대기중... |`);
          win.console.log('📋 ==========================================');
          win.console.log('👤 사용자 안내:');
          win.console.log('📋 1. 위의 스크린샷에서 6글자 캡차를 확인하세요');
          win.console.log('📋 2. 6글자 캡차를 입력하세요 (예: ABC123)');
          win.console.log('📋 3. 입력이 완료되면 Enter 키를 눌러주세요');
          
          // 브라우저에 표시하기 위해 alert도 추가
          win.alert('📋 실시간 캡차 처리 표\n\n' +
                   '사건 번호: ' + caseNumber + '\n' +
                   '캡차 이미지: realtime-captcha-image.png\n\n' +
                   '브라우저 개발자 도구(F12) > Console 탭에서\n' +
                   '실시간 처리 표를 확인하세요!');
        });
        
        // 파이썬 입력창을 통한 사용자 입력
        cy.exec('python captcha_input.py', { 
          failOnNonZeroExit: false,
          timeout: 60000 
        }).then((result) => {
          cy.log(`🐍 파이썬 실행 결과:`, result);
          cy.log(`🐍 stdout: "${result.stdout}"`);
          cy.log(`🐍 stderr: "${result.stderr}"`);
          cy.log(`🐍 exitCode: ${result.code}`);
          
          const userInput = result.stdout.trim();
          cy.log(`🐍 파이썬 입력창 결과: "${userInput}"`);
          
          if (userInput && userInput.length === 6) {
            cy.log(`✅ 사용자 입력 받음: "${userInput}"`);
            
            // 실시간 처리 표 업데이트
            cy.log('📋 ==========================================');
            cy.log('📋 실시간 캡차 처리 표 (업데이트됨)');
            cy.log('📋 ==========================================');
            cy.log('📋 | 사건 번호 | 캡차 이미지 | 사용자 입력 |');
            cy.log('📋 |----------|-------------|-------------|');
            cy.log(`📋 | ${caseNumber} | realtime-captcha-image.png | ${userInput} |`);
            cy.log('📋 ==========================================');
            cy.log('🔄 자동 처리 시작...');
            
            // 캡차 입력 필드에 사용자가 입력한 값 입력
            cy.get('#mf_ssgoTopMainTab_contents_content1_body_ibx_answer').then($input => {
              cy.log('📝 사용자 입력 캡차를 자동으로 입력합니다...');
              cy.wrap($input).clear({ force: true });
              cy.wait(500);
              
              // 한 글자씩 입력하여 로그 확인
              const chars = userInput.split('');
              chars.forEach((char, index) => {
                cy.wrap($input).type(char, { force: true, delay: 150 });
                cy.log(`🔤 캡차 글자 ${index + 1}/${chars.length}: "${char}" 입력`);
                cy.wait(100);
              });
              
              cy.wait(1000);
              cy.wrap($input).then($updated => {
                const inputValue = $updated.val();
                cy.log(`✅ 사용자 입력 캡차 입력 완료: "${inputValue}"`);
                
                if (inputValue === userInput) {
                  cy.log('✅ 사용자 입력 캡차 정확히 입력됨!');
                } else {
                  cy.log(`⚠️ 사용자 입력 캡차 불일치: 예상 "${userInput}", 실제 "${inputValue}"`);
                }
              });
            });
            
            // 캡차 입력 후 스크린샷
            cy.log('📸 캡차 입력 후 스크린샷');
            cy.screenshot('realtime-captcha-after-input');
            
            // 실시간 처리 표 최종 업데이트
            cy.log('📋 ==========================================');
            cy.log('📋 실시간 캡차 처리 표 (완료)');
            cy.log('📋 ==========================================');
            cy.log('📋 | 사건 번호 | 캡차 이미지 | 사용자 입력 | 상태 |');
            cy.log('📋 |----------|-------------|-------------|------|');
            cy.log(`📋 | ${caseNumber} | realtime-captcha-image.png | ${userInput} | 완료 |`);
            cy.log('📋 ==========================================');
            
          } else {
            cy.log('❌ 사용자 입력이 없거나 6글자가 아닙니다');
            cy.log('🔄 파이썬 입력창으로 다시 시도합니다');
            
            // 파이썬 입력창으로 재시도
            cy.exec('python captcha_input.py', { 
              failOnNonZeroExit: false,
              timeout: 60000 
            }).then((retryResult) => {
              cy.log(`🐍 재시도 파이썬 실행 결과:`, retryResult);
              const retryInput = retryResult.stdout.trim();
              cy.log(`🐍 재시도 파이썬 입력창 결과: "${retryInput}"`);
              
              if (retryInput && retryInput.length === 6) {
                cy.log(`✅ 재시도 사용자 입력 받음: "${retryInput}"`);
                
                cy.get('#mf_ssgoTopMainTab_contents_content1_body_ibx_answer').then($input => {
                  cy.wrap($input).clear({ force: true });
                  cy.wrap($input).type(retryInput, { force: true });
                  cy.log('✅ 재시도 캡차 입력 완료');
                });
              } else {
                cy.log('❌ 재시도도 실패 - 테스트 중단');
                cy.log('💡 수동으로 캡차를 입력해주세요');
                return;
              }
            });
          }
        });
        
      } else {
        cy.log('ℹ️ 캡차 이미지가 없음');
      }
    });
    
    cy.wait(3000);
    
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
      cy.get('body').then($body => {
        const visibleInputs = $body.find('input[type="text"]:visible');
        if (visibleInputs.length > 0) {
          cy.get('input[type="text"]:visible').first().type('{enter}', { force: true });
        } else {
          cy.log('⚠️ 입력 필드를 찾을 수 없음 - 검색 건너뛰기');
        }
      });
    }
    
    // 결과 대기
    cy.wait(5000);
    
    // 7단계: 최종 결과 스크린샷
    cy.log('🎯 7단계: 최종 결과 스크린샷');
    cy.screenshot('realtime-captcha-final-result');
    
    // 8단계: 결과 확인
    cy.log('🎯 8단계: 실시간 캡차 결과 확인');
    cy.get('body').then($body => {
      const bodyText = $body.text();
      
      if (bodyText.includes('자동입력방지') || bodyText.includes('보안문자') || bodyText.includes('잘못')) {
        cy.log('❌ 실시간 캡차 실패 감지됨');
        cy.log('💡 캡차를 다시 확인해주세요');
      } else if (bodyText.includes('검색결과') || bodyText.includes('사건정보')) {
        cy.log('✅ 실시간 캡차 성공! 검색 완료!');
      } else {
        cy.log('ℹ️ 실시간 캡차 결과 불명확');
      }
    });
    
    cy.log('🎉 실시간 캡차 자동화 완료!');
    cy.log('👤 사용자가 실시간으로 캡차를 입력하고 자동화가 처리했습니다!');
    
    // 자동 종료 방지 - 사용자가 로그를 확인할 수 있도록 대기
    cy.log('⏳ 로그 확인을 위해 60초 대기 중...');
    cy.log('📋 ==========================================');
    cy.log('📋 실시간 캡차 처리 완료!');
    cy.log('📋 ==========================================');
    cy.log('📋 브라우저를 수동으로 종료하세요');
    cy.log('📋 ==========================================');
    cy.wait(60000);
    cy.log('✅ 대기 완료 - 브라우저를 수동으로 종료하세요');
  });
});


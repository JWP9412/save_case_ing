describe('실시간 대화형 캡차 자동화', function () {
  // 테스트 시작 전에 구글시트에서 최신 데이터 가져오기
  before(function() {
    cy.log('구글시트에서 최신 데이터를 가져오는 중...');
    cy.exec('python create-fixtures-python.py', { 
      failOnNonZeroExit: false,
      timeout: 30000 
    }).then((result) => {
      cy.log('구글시트 데이터 가져오기 완료');
      cy.log(`stdout: ${result.stdout}`);
      if (result.stderr) {
        cy.log(`stderr: ${result.stderr}`);
      }
    });
  });
  
  // 구글시트에서 모든 항목을 읽어와서 반복 실행
  it('실시간 캡차 자동화 - 모든 사건 처리', function() {
    // 최신 데이터 로드
    cy.readFile('cypress/fixtures/cases_chunk_0.json').then((cases) => {
      cy.log(`구글시트에서 ${cases.length}개의 사건을 읽어왔습니다`);
      
      // 각 사건별로 처리
      cases.forEach((caseData, index) => {
        const [rowIndex, court, caseNumber, manager] = caseData;
        
        cy.log(`처리할 사건: ${court} ${caseNumber} (${manager}) - ${index + 1}/${cases.length}`);
        
        // 간편 사이트 접속
        cy.visit('https://ssgo.scourt.go.kr/ssgo/index.on?cortId=www');
        cy.wait(1250);
        cy.log('사이트 접속 완료');
        
        // 1단계: 체크박스 체크
        cy.log('2단계: 사건번호입력모드 체크박스 체크');
        cy.get('#mf_ssgoTopMainTab_contents_content1_body_cbx_chkSanoInputMode_input_0', { timeout: 10000 }).should('be.visible').check({ force: true });
        cy.log('체크박스 체크 완료');
        cy.wait(500);
        
        // 2단계: 법원 선택
        cy.log(`1단계: 법원 선택 - ${court}`);
        cy.get('body').then($body => {
          const selects = $body.find('select');
          selects.each((index, select) => {
            const options = [];
            for (let i = 0; i < select.options.length; i++) {
              options.push(select.options[i].text);
            }
            const courtIndex = options.findIndex(opt => opt.includes(court));
            if (courtIndex >= 0) {
              cy.log(`${court} 발견! 인덱스: ${courtIndex}`);
              cy.get(select).select(courtIndex, { force: true });
              cy.log(`${court} 선택 완료`);
              return false;
            }
          });
        });
        
        cy.wait(1000);
        
        // 3단계: 사건번호 입력
        cy.log('3단계: 사건번호 입력');
        cy.get('input[type="text"]:visible').first().then($input => {
          cy.wrap($input).clear({ force: true });
          cy.wrap($input).type(caseNumber, { force: true, delay: 50 });
          cy.log(`사건번호 입력: "${caseNumber}"`);
        });
        
        cy.wait(500);
        
        // 4단계: 당사자명 입력
        cy.log('4단계: 당사자명 입력');
        cy.get('body').then($body => {
          const visibleInputs = $body.find('input[type="text"]:visible');
          if (visibleInputs.length > 1) {
            cy.get('input[type="text"]:visible').eq(1).then($input => {
              cy.wrap($input).clear({ force: true });
              cy.wrap($input).type(manager, { force: true, delay: 50 });
              cy.log(`당사자명 입력: "${manager}"`);
            });
          }
        });
        cy.wait(500);
        
        // 5단계: 실시간 캡차 처리
        cy.log('5단계: 실시간 캡차 처리');
        cy.get('body').then($body => {
          const captchaImage = $body.find('#mf_ssgoTopMainTab_contents_content1_body_img_captcha');
          if (captchaImage.length > 0) {
            cy.log('6글자 캡차 이미지 발견됨');
            
            // 캡차 이미지만 따로 캡처 (사건번호+날짜+시간)
            cy.log('캡차 이미지만 따로 캡처');
            const now = new Date();
            const dateStr = now.toISOString().slice(0, 10).replace(/-/g, ''); // YYYYMMDD
            const timeStr = now.toTimeString().slice(0, 8).replace(/:/g, ''); // HHMMSS
            const imageName = `${caseNumber}-${dateStr}-${timeStr}`;
            cy.get('#mf_ssgoTopMainTab_contents_content1_body_img_captcha').screenshot(imageName);
            cy.log(`캡처된 이미지: ${imageName}.png`);
            
            // 파이썬 입력창을 통한 사용자 입력 (사건번호 전달)
            cy.exec(`python captcha_input.py ${caseNumber}`, { 
              failOnNonZeroExit: false,
              timeout: 60000 
            }).then((result) => {
              cy.log(`파이썬 실행 결과:`, result);
              const userInput = result.stdout.trim();
              cy.log(`파이썬 입력창 결과: "${userInput}"`);
              
              let actualInput = userInput;
              if (userInput.includes("SUCCESS:")) {
                actualInput = userInput.split("SUCCESS:")[1].trim();
                cy.log(`SUCCESS에서 추출한 값: "${actualInput}"`);
              }
              
              if (actualInput && actualInput.length === 6 && !actualInput.includes("ERROR")) {
                cy.log(`사용자 입력 받음: "${actualInput}"`);
                
                // 캡차 입력 필드에 입력
                cy.get('#mf_ssgoTopMainTab_contents_content1_body_ibx_answer').then($input => {
                  cy.wrap($input).clear({ force: true });
                  cy.wrap($input).type(actualInput, { force: true, delay: 100 });
                  cy.log(`캡차 입력 완료: "${actualInput}"`);
                });
                
                // 캡차 입력 후 스크린샷
                cy.log('캡차 입력 후 스크린샷');
                const now = new Date();
                const dateStr = now.toISOString().slice(0, 10).replace(/-/g, ''); // YYYYMMDD
                const timeStr = now.toTimeString().slice(0, 8).replace(/:/g, ''); // HHMMSS
                const processImageName = `${caseNumber}-${dateStr}-${timeStr}-process`;
                cy.screenshot(processImageName);
                
              } else {
                cy.log('사용자 입력이 없거나 6글자가 아닙니다');
              }
            });
          } else {
            cy.log('캡차 이미지를 찾을 수 없습니다');
          }
        });
        
        cy.wait(1500);
        
        // 6단계: 검색 버튼 클릭
        cy.log('6단계: 검색 버튼 클릭');
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
              cy.log(`검색 버튼 발견: ${selector}`);
              cy.get(selector).first().click({ force: true });
              cy.log('검색 버튼 클릭 완료');
              searchButtonFound = true;
            }
          });
        });
        
        if (!searchButtonFound) {
          cy.log('검색 버튼을 찾을 수 없음 - Enter 키 시도');
          cy.get('body').then($body => {
            const visibleInputs = $body.find('input[type="text"]:visible');
            if (visibleInputs.length > 0) {
              cy.get('input[type="text"]:visible').first().type('{enter}', { force: true });
            } else {
              cy.log('입력 필드를 찾을 수 없음 - 검색 건너뛰기');
            }
          });
        }
        
        // 결과 대기
        cy.wait(2500);
        
        // 7단계: 진행내용 탭 클릭 (선택적)
        cy.log('7단계: 진행내용 탭 클릭 시도');
        cy.get('body').then($body => {
          const progressTab = $body.find('#mf_ssgoTopMainTab_contents_content1_body_wfSsgoDetail_ssgoCsDetailTab_tab_ssgoTab2');
          if (progressTab.length > 0) {
            cy.get('#mf_ssgoTopMainTab_contents_content1_body_wfSsgoDetail_ssgoCsDetailTab_tab_ssgoTab2', { timeout: 10000 }).should('be.visible').click({ force: true });
            cy.log('진행내용 탭 클릭 완료');
            cy.wait(1000);
          } else {
            cy.log('진행내용 탭을 찾을 수 없음 - 건너뛰기');
          }
        });
        
        // 8단계: 최종 결과 스크린샷
        cy.log('8단계: 최종 결과 스크린샷');
        const now = new Date();
        const dateStr = now.toISOString().slice(0, 10).replace(/-/g, ''); // YYYYMMDD
        const timeStr = now.toTimeString().slice(0, 8).replace(/:/g, ''); // HHMMSS
        const finalImageName = `${caseNumber}-${dateStr}-${timeStr}-final`;
        cy.screenshot(finalImageName);
        
        cy.log(`사건 ${caseNumber} 처리 완료!`);
        cy.wait(1000); // 다음 사건 처리 전 대기
      });
    });
  });
});
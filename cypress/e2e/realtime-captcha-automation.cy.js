/**
 * 실시간 대화형 캡차 자동화 테스트
 * =====================================
 * 
 * 역할: 대법원 나의 사건 조회 사이트에서 실시간으로 캡차를 처리하는 자동화 테스트
 * 기능:
 * - 구글시트에서 사건 데이터를 읽어와서 처리
 * - 각 사건별로 사이트 접속, 정보 입력, 캡차 처리
 * - 사용자가 직접 캡차를 입력할 수 있는 GUI 창 제공
 * - 처리 결과를 스크린샷으로 저장
 * 
 * 사용법: npm test 또는 cypress run
 */

describe('실시간 대화형 캡차 자동화', function () {
  // ========================================
  // 유틸리티 함수들
  // ========================================
  
  /**
   * 드롭다운의 모든 선택지를 분석하는 함수
   * 
   * @param {jQuery} $select - 분석할 select 요소
   * @param {string} selectName - 드롭다운 이름 (로그용)
   * @returns {Object} 분석 결과 객체
   */
  function analyzeDropdown($select, selectName = '드롭다운') {
    const options = [];
    const optionValues = [];
    
    // 모든 옵션 정보 수집
    for (let i = 0; i < $select[0].options.length; i++) {
      const option = $select[0].options[i];
      options.push({
        index: i,
        text: option.text,
        value: option.value,
        selected: option.selected,
        disabled: option.disabled
      });
      optionValues.push(option.value);
    }
    
    // 분석 결과 반환
    return {
      name: selectName,
      totalOptions: options.length,
      options: options,
      values: optionValues,
      selectedIndex: $select[0].selectedIndex,
      selectedText: options[$select[0].selectedIndex]?.text || '없음'
    };
  }
  
  /**
   * 모든 드롭다운을 찾아서 분석하는 함수
   * 
   * @param {jQuery} $body - 페이지 body 요소
   * @returns {Array} 모든 드롭다운 분석 결과 배열
   */
  function analyzeAllDropdowns($body) {
    const selects = $body.find('select');
    const results = [];
    
    selects.each((index, select) => {
      const $select = Cypress.$(select);
      const analysis = analyzeDropdown($select, `드롭다운 ${index + 1}`);
      results.push(analysis);
    });
    
    return results;
  }
  
  // ========================================
  // 테스트 시작 전 준비 작업
  // ========================================
  
  /**
   * 테스트 시작 전에 구글시트에서 최신 데이터 가져오기
   * - create-fixtures-python.py 스크립트를 실행하여 구글시트 데이터를 JSON 파일로 변환
   * - 이 데이터는 각 사건의 정보(법원, 사건번호, 담당자명)를 포함
   */
  before(function() {
    cy.log('구글시트에서 최신 데이터를 가져오는 중...');
    
    // Python 스크립트 실행하여 구글시트 데이터를 fixtures로 변환
    cy.exec('py create-fixtures-python.py', { 
      failOnNonZeroExit: false,  // Python 스크립트 실패해도 테스트 계속 진행
      timeout: 30000            // 30초 타임아웃 (구글시트 API 호출 시간 고려)
    }).then((result) => {
      cy.log('구글시트 데이터 가져오기 완료');
      cy.log(`stdout: ${result.stdout}`);  // Python 스크립트의 표준 출력
      if (result.stderr) {
        cy.log(`stderr: ${result.stderr}`); // Python 스크립트의 오류 출력
      }
    });
  });
  
  // ========================================
  // 메인 테스트 케이스
  // ========================================
  
  /**
   * 실시간 캡차 자동화 - 모든 사건 처리
   * 
   * 이 테스트는 구글시트에서 읽어온 모든 사건 데이터를 순차적으로 처리합니다.
   * 각 사건에 대해 다음 단계를 수행:
   * 1. 대법원 사이트 접속
   * 2. 사건 정보 입력 (법원, 사건번호, 담당자명)
   * 3. 캡차 이미지 캡처 및 사용자 입력 요청
   * 4. 검색 실행 및 결과 확인
   */
  it('실시간 캡차 자동화 - 모든 사건 처리', function() {
    // ========================================
    // 1. 테스트 데이터 로드
    // ========================================
    
    // 구글시트에서 생성된 JSON 파일에서 사건 데이터 읽기
    // cases_chunk_0.json: 첫 번째 청크의 사건 데이터 (5개씩 나누어 저장됨)
    cy.readFile('cypress/fixtures/cases_chunk_0.json').then((cases) => {
      cy.log(`구글시트에서 ${cases.length}개의 사건을 읽어왔습니다`);
      
      // ========================================
      // 2. 각 사건별 순차 처리
      // ========================================
      
      // forEach를 사용하여 각 사건을 순차적으로 처리
      // caseData: [행번호, 법원명, 사건번호, 담당자명] 형태의 배열
      cases.forEach((caseData, index) => {
        // 배열 구조분해할당으로 각 값 추출
        const [rowIndex, court, caseNumber, manager] = caseData;
        
        cy.log(`처리할 사건: ${court} ${caseNumber} (${manager}) - ${index + 1}/${cases.length}`);
        
        // ========================================
        // 3. 대법원 사이트 접속
        // ========================================
        
        // 대법원 나의 사건 조회 사이트 접속
        // ssgo.scourt.go.kr: 대법원 간편 사이트
        // cortId=www: 웹 버전 접속
        cy.visit('https://ssgo.scourt.go.kr/ssgo/index.on?cortId=www');
        
        // 페이지 로딩 완료까지 대기 (동적 대기)
        cy.get('body', { timeout: 10000 }).should('be.visible');
        cy.log('사이트 접속 완료');
        
        // ========================================
        // 4. 사건번호 입력 모드 활성화
        // ========================================
        
        // 사건번호 직접 입력 모드로 전환하는 체크박스 클릭
        // 이 체크박스를 체크해야 사건번호를 직접 입력할 수 있음
        cy.log('4단계: 사건번호입력모드 체크박스 체크');
        
        // 체크박스가 존재하는지 먼저 확인
        cy.get('#mf_ssgoTopMainTab_contents_content1_body_cbx_chkSanoInputMode_input_0', { timeout: 10000 })
          .should('be.visible')
          .then(($checkbox) => {
            cy.log('체크박스 발견됨, 현재 상태:', $checkbox.is(':checked'));
            
            // 체크박스가 이미 체크되어 있지 않다면 클릭
            if (!$checkbox.is(':checked')) {
              cy.log('체크박스가 체크되지 않음, 클릭 시도');
              
              // 방법 1: 일반 클릭
              cy.wrap($checkbox).click({ force: true });
              cy.log('첫 번째 클릭 완료');
              
              // 잠시 대기
              cy.wait(1000);
              
              // 방법 2: JavaScript로 직접 체크
              cy.wrap($checkbox).then(($el) => {
                $el[0].checked = true;
                $el.trigger('change');
                $el.trigger('click');
                cy.log('JavaScript로 체크 시도');
              });
              
              // 잠시 대기
              cy.wait(1000);
              
              // 방법 3: 다시 클릭
              cy.wrap($checkbox).click({ force: true });
              cy.log('두 번째 클릭 완료');
              
              // 충분한 대기
              cy.wait(2000);
              
              // 체크박스 상태 확인 (에러가 나도 계속 진행)
              cy.get('#mf_ssgoTopMainTab_contents_content1_body_cbx_chkSanoInputMode_input_0')
                .then(($el) => {
                  const isChecked = $el.is(':checked');
                  cy.log('최종 체크 상태:', isChecked);
                  if (!isChecked) {
                    cy.log('⚠️ 체크박스가 여전히 체크되지 않음, 강제로 진행');
                  }
                });
            } else {
              cy.log('체크박스가 이미 체크되어 있음');
            }
          });
        
        // 체크박스 체크 완료 후 추가 대기 (페이지 업데이트)
        cy.wait(2000);
        cy.log('체크박스 체크 완료');
        
      // ========================================
      // 5. 법원 선택
      // ========================================
      
      // 구글시트에서 읽어온 법원명으로 드롭다운에서 해당 법원 선택
      // 예: "서울고등법원", "서울중앙지방법원" 등
      cy.log(`5단계: 법원 선택 - ${court}`);
      cy.get('body').then($body => {
        // 페이지의 모든 select 요소 찾기
        const selects = $body.find('select');
        let courtFound = false;
        
        // 각 select 요소를 순회하며 법원명이 포함된 옵션 찾기
        selects.each((index, select) => {
          if (courtFound) return false; // 이미 찾았으면 중단
          
          const options = [];
          // select의 모든 옵션 텍스트를 배열로 수집
          for (let i = 0; i < select.options.length; i++) {
            options.push(select.options[i].text);
          }
          
          // 법원명이 포함된 옵션의 인덱스 찾기 (부분 매칭)
          const courtIndex = options.findIndex(opt => opt.includes(court));
          if (courtIndex >= 0) {
            cy.log(`✅ ${court} 발견! 선택 중...`);
            
            // 해당 인덱스로 select 값 변경
            cy.get(select).select(courtIndex, { force: true });
            cy.log(`${court} 선택 완료`);
            courtFound = true;
            return false;  // 찾았으면 each 루프 종료
          }
        });
        
        // 법원을 찾지 못한 경우
        if (!courtFound) {
          cy.log(`❌ ${court}를 찾을 수 없습니다.`);
        }
      });
      
      // 법원 선택 후 페이지 업데이트 대기 (동적 대기)
      cy.get('body').should('be.visible');  // 페이지가 준비될 때까지 대기
        
        // ========================================
        // 6. 사건번호 입력
        // ========================================
        
        // 구글시트에서 읽어온 사건번호를 사건번호 전용 입력 필드에 입력
        // 예: "2024가합51101", "2023나10019" 등
        cy.log('6단계: 사건번호 입력');
        
        // 사건번호 입력 필드를 찾아서 입력
        cy.get('#mf_ssgoTopMainTab_contents_content1_body_ibx_fullCsNo', { timeout: 10000 })
          .should('be.visible')
          .clear({ force: true })  // 기존 내용 삭제
          .type(caseNumber, { 
            force: true,  // 강제 입력 (다른 요소에 가려져 있어도)
            delay: 100    // 각 글자 입력 간 100ms 지연 (자연스러운 타이핑)
          });
        
        cy.log(`사건번호 입력: "${caseNumber}"`);
        
        // 사건번호 입력 완료 확인 (동적 대기)
        cy.get('#mf_ssgoTopMainTab_contents_content1_body_ibx_fullCsNo')
          .should('have.value', caseNumber);
        
        // ========================================
        // 7. 당사자명(담당자명) 입력
        // ========================================
        
        // 구글시트에서 읽어온 담당자명을 두 번째 텍스트 입력 필드에 입력
        // 담당자명은 사건의 당사자 이름으로, 검색 정확도를 높이기 위해 사용
        cy.log('7단계: 당사자명 입력');
        cy.get('body').then($body => {
          const visibleInputs = $body.find('input[type="text"]:visible');
          if (visibleInputs.length > 1) {
            // 두 번째 텍스트 입력 필드에 담당자명 입력
            cy.get('input[type="text"]:visible').eq(1).then($input => {
              cy.wrap($input).clear({ force: true });  // 기존 내용 삭제
              cy.wrap($input).type(manager, { 
                force: true,  // 강제 입력
                delay: 50     // 각 글자 입력 간 50ms 지연
              });
              cy.log(`당사자명 입력: "${manager}"`);
            });
            
            // 당사자명 입력 완료 확인 (동적 대기)
            cy.get('input[type="text"]:visible').eq(1).should('have.value', manager);
          }
        });
        
        // ========================================
        // 8. 실시간 캡차 처리 (핵심 기능)
        // ========================================
        
        // 이 부분이 이 테스트의 핵심 기능입니다.
        // 캡차 이미지를 감지하고, 사용자가 직접 입력할 수 있는 GUI 창을 띄워서 처리합니다.
        cy.log('8단계: 실시간 캡차 처리');
        cy.get('body').then($body => {
          // 캡차 이미지 요소 찾기 (ID로 정확한 요소 선택)
          const captchaImage = $body.find('#mf_ssgoTopMainTab_contents_content1_body_img_captcha');
          
          if (captchaImage.length > 0) {
            cy.log('6글자 캡차 이미지 발견됨');
            
            // ========================================
            // 8-1. 캡차 이미지 스크린샷 캡처
            // ========================================
            
            // 캡차 이미지만 따로 캡처하여 사용자가 볼 수 있도록 저장
            // 파일명 형식: "사건번호-YYYYMMDD-HHMMSS.png"
            cy.log('캡차 이미지만 따로 캡처');
            const now = new Date();
            const dateStr = now.toISOString().slice(0, 10).replace(/-/g, ''); // YYYYMMDD 형식
            const timeStr = now.toTimeString().slice(0, 8).replace(/:/g, ''); // HHMMSS 형식
            const imageName = `${caseNumber}-${dateStr}-${timeStr}`;
            
            // 캡차 이미지 요소만 스크린샷으로 캡처
            cy.get('#mf_ssgoTopMainTab_contents_content1_body_img_captcha').screenshot(imageName);
            cy.log(`캡처된 이미지: ${imageName}.png`);
            
            // ========================================
            // 8-2. 파이썬 GUI 입력창 실행
            // ========================================
            
            // 리팩토링된 captcha_input.py를 실행하여 사용자에게 캡차 입력 GUI 제공
            // 사건번호를 인수로 전달하여 해당 사건의 캡차 이미지를 찾아서 표시
            cy.exec(`py captcha_input.py ${caseNumber}`, { 
              failOnNonZeroExit: false,  // 파이썬 스크립트 실패해도 테스트 계속 진행
              timeout: 60000            // 60초 타임아웃 (사용자 입력 대기 시간 고려)
            }).then((result) => {
              cy.log(`=== 파이썬 실행 결과 디버깅 ===`);
              cy.log(`stdout: "${result.stdout}"`);
              cy.log(`stderr: "${result.stderr}"`);
              cy.log(`exitCode: ${result.code}`);
              cy.log(`killed: ${result.killed}`);
              cy.log(`signal: ${result.signal}`);
              
              const userInput = result.stdout.trim();  // 파이썬 스크립트의 출력 결과
              cy.log(`파이썬 입력창 결과: "${userInput}"`);
              
              // ========================================
              // 8-3. 사용자 입력 결과 처리
              // ========================================
              
              let actualInput = userInput;
              // SUCCESS: 로 시작하는 경우 실제 입력값만 추출
              if (userInput.includes("SUCCESS:")) {
                // SUCCESS: 뒤의 텍스트에서 첫 번째 줄만 추출 (6글자 캡차만)
                const successPart = userInput.split("SUCCESS:")[1].trim();
                actualInput = successPart.split('\n')[0].trim(); // 첫 번째 줄만 가져오기
                cy.log(`SUCCESS에서 추출한 값: "${actualInput}"`);
              }
              
              // 입력값 유효성 검증 (6글자이고 오류가 아닌 경우)
              if (actualInput && actualInput.length === 6 && !actualInput.includes("ERROR")) {
                cy.log(`사용자 입력 받음: "${actualInput}"`);
                
                // ========================================
                // 8-4. 캡차 입력 필드에 사용자 입력값 입력
                // ========================================
                
                // 웹사이트의 캡차 입력 필드에 사용자가 입력한 6글자 입력
                cy.get('#mf_ssgoTopMainTab_contents_content1_body_ibx_answer').then($input => {
                  cy.wrap($input).clear({ force: true });  // 기존 내용 삭제
                  cy.wrap($input).type(actualInput, { 
                    force: true,   // 강제 입력
                    delay: 100     // 각 글자 입력 간 100ms 지연
                  });
                  cy.log(`캡차 입력 완료: "${actualInput}"`);
                });
                
                // ========================================
                // 8-5. 캡차 입력 후 상태 스크린샷
                // ========================================
                
                // 캡차 입력이 완료된 상태를 스크린샷으로 저장
                cy.log('캡차 입력 후 스크린샷');
                const now = new Date();
                const dateStr = now.toISOString().slice(0, 10).replace(/-/g, ''); // YYYYMMDD
                const timeStr = now.toTimeString().slice(0, 8).replace(/:/g, ''); // HHMMSS
                const processImageName = `${caseNumber}-${dateStr}-${timeStr}-process`;
                cy.screenshot(processImageName);  // 전체 페이지 스크린샷
                
              } else {
                // 입력값이 유효하지 않은 경우 (6글자가 아니거나 오류)
                cy.log('사용자 입력이 없거나 6글자가 아닙니다');
              }
            });
          } else {
            cy.log('캡차 이미지를 찾을 수 없습니다');
          }
        });
        
        // 캡차 처리 완료 후 페이지 준비 대기 (동적 대기)
        cy.get('body').should('be.visible');
        
        // ========================================
        // 9. 검색 버튼 클릭
        // ========================================
        
        // 모든 정보 입력이 완료되었으므로 검색을 실행
        // 여러 가지 검색 버튼 선택자를 시도하여 호환성 확보
        cy.log('9단계: 검색 버튼 클릭');
        const searchButtonSelectors = [
          'input[type="submit"]',                    // 일반적인 submit 버튼
          'input[type="button"][value*="검색"]',     // "검색" 텍스트가 포함된 버튼
          'input[type="button"][value*="조회"]',     // "조회" 텍스트가 포함된 버튼
          'button:contains("검색")',                 // "검색" 텍스트를 포함한 button 요소
          'button:contains("조회")'                  // "조회" 텍스트를 포함한 button 요소
        ];
        
        let searchButtonFound = false;
        // 각 선택자를 순차적으로 시도하여 검색 버튼 찾기
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
        
        // 검색 버튼을 찾지 못한 경우 Enter 키로 검색 시도
        if (!searchButtonFound) {
          cy.log('검색 버튼을 찾을 수 없음 - Enter 키 시도');
          cy.get('body').then($body => {
            const visibleInputs = $body.find('input[type="text"]:visible');
            if (visibleInputs.length > 0) {
              // 첫 번째 입력 필드에서 Enter 키 입력
              cy.get('input[type="text"]:visible').first().type('{enter}', { force: true });
            } else {
              cy.log('입력 필드를 찾을 수 없음 - 검색 건너뛰기');
            }
          });
        }
        
        // ========================================
        // 10. 검색 결과 대기
        // ========================================
        
        // 검색 실행 후 결과 페이지 로딩 대기 (동적 대기)
        cy.get('body', { timeout: 15000 }).should('be.visible');
        
        // ========================================
        // 11. 진행내용 탭 클릭 및 데이터 추출
        // ========================================
        
        // 검색 결과에서 더 자세한 정보를 보기 위해 진행내용 탭 클릭 시도
        // 이 탭이 있으면 사건의 진행 상황을 더 자세히 볼 수 있음
        cy.log('11단계: 진행내용 탭 클릭 및 데이터 추출');
        cy.get('body').then($body => {
          const progressTab = $body.find('#mf_ssgoTopMainTab_contents_content1_body_wfSsgoDetail_ssgoCsDetailTab_tab_ssgoTab2');
          if (progressTab.length > 0) {
            // 진행내용 탭이 존재하면 클릭
            cy.wrap(progressTab)
              .should('be.visible')
              .click({ force: true });
            cy.log('진행내용 탭 클릭 완료');
            
            // 탭 전환 완료 확인 (동적 대기)
            cy.get('body').should('be.visible');
            
            // ========================================
            // 11-1. 진행내용 그리드 데이터 추출
            // ========================================
            
            // 진행내용 그리드가 로드될 때까지 대기
            cy.get('#mf_ssgoTopMainTab_contents_content1_body_wfSsgoDetail_ssgoCsDetailTab_contents_ssgoTab2_body_grd_csProgLst_main_div', { timeout: 10000 })
              .should('be.visible')
              .then(($grid) => {
                cy.log('진행내용 그리드 발견됨, 데이터 추출 시작');
                
                // 그리드 내의 테이블 데이터 추출
                const progressData = {
                  caseNumber: caseNumber,
                  extractedAt: new Date().toISOString(),
                  rows: []
                };
                
                // 테이블의 모든 행 찾기
                const rows = $grid.find('tbody tr');
                cy.log(`발견된 행 수: ${rows.length}`);
                
                // 각 행의 데이터 추출
                rows.each((index, row) => {
                  const $row = Cypress.$(row);
                  const cells = $row.find('td');
                  
                  if (cells.length >= 4) {
                    const rowData = {
                      date: cells.eq(0).find('span').text().trim(),
                      content: cells.eq(1).find('span').text().trim(),
                      result: cells.eq(2).find('span').text().trim(),
                      document: cells.eq(3).find('span').text().trim()
                    };
                    
                    // 빈 행이 아닌 경우만 추가
                    if (rowData.date || rowData.content) {
                      progressData.rows.push(rowData);
                    }
                  }
                });
                
                cy.log(`추출된 진행내용 행 수: ${progressData.rows.length}`);
                
                // ========================================
                // 11-2. 추출된 데이터를 JSON 파일로 저장
                // ========================================
                
                // JSON 데이터를 파일로 저장
                const jsonData = JSON.stringify(progressData, null, 2);
                const filename = `progress_data_${caseNumber}.json`;
                
                cy.writeFile(filename, jsonData).then(() => {
                  cy.log(`진행내용 데이터 저장 완료: ${filename}`);
                  
                  // ========================================
                  // 11-3. 구글 시트에 진행내용 데이터 저장
                  // ========================================
                  
                  // 구글 시트 저장 시도 (선택적)
                  cy.exec(`py progress-extractor.py ${caseNumber}`, { 
                    failOnNonZeroExit: false,  // Python 스크립트 실패해도 테스트 계속 진행
                    timeout: 30000            // 30초 타임아웃
                  }).then((result) => {
                    cy.log(`=== 진행내용 데이터 구글 시트 저장 결과 ===`);
                    cy.log(`stdout: ${result.stdout}`);
                    if (result.stderr) {
                      cy.log(`stderr: ${result.stderr}`);
                    }
                    cy.log(`exitCode: ${result.code}`);
                    
                    if (result.code === 0) {
                      cy.log('✅ 진행내용 데이터가 구글 시트에 성공적으로 저장되었습니다');
                    } else {
                      cy.log('⚠️ 구글 시트 저장에 실패했지만 JSON 파일은 저장되었습니다');
                      cy.log('📁 JSON 파일 위치: progress_data_' + caseNumber + '.json');
                    }
                  });
                });
              });
          } else {
            cy.log('진행내용 탭을 찾을 수 없음 - 건너뛰기');
          }
        });
        
        // ========================================
        // 12. 최종 결과 스크린샷
        // ========================================
        
        // 모든 처리가 완료된 최종 상태를 스크린샷으로 저장
        // 파일명 형식: "사건번호-YYYYMMDD-HHMMSS-final.png"
        cy.log('12단계: 최종 결과 스크린샷');
        const now = new Date();
        const dateStr = now.toISOString().slice(0, 10).replace(/-/g, ''); // YYYYMMDD 형식
        const timeStr = now.toTimeString().slice(0, 8).replace(/:/g, ''); // HHMMSS 형식
        const finalImageName = `${caseNumber}-${dateStr}-${timeStr}-final`;
        cy.screenshot(finalImageName);  // 전체 페이지 최종 스크린샷
        
        // ========================================
        // 13. 사건 처리 완료
        // ========================================
        
        cy.log(`사건 ${caseNumber} 처리 완료!`);
        // 다음 사건 처리 전 최소 대기 (서버 부하 방지)
        cy.wait(500);
        cy.log(`프로그램 완료!`);
      });
    });
  });
});
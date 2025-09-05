// Lambda API 기반 case-ing 자동화 스크립트
const cases = require('../fixtures/cases_chunk_0.json');

const LAMBDA_API_URL = Cypress.env('CYPRESS_LAMBDA_API_URL');
const S3_BUCKET_URL = Cypress.env('CYPRESS_S3_BUCKET_URL');
const SCREENSHOT_URL = `${S3_BUCKET_URL}/screenshots`;

describe('Case-ing Lambda API 자동화', () => {
  let caseLookup = {};
  let doneCaseLookup = {};

  it('완전한 사건검색 자동화', () => {
    
    // 테스트용으로 첫 번째 사건만 처리
    const [rowIndex, court, caseNumber, manager] = cases[0];
    
    cy.log(`🔍 테스트 사건: ${court} ${caseNumber} (${manager})`);
    
    // cases.forEach(([rowIndex, court, caseNumber, manager]) => {
      cy.log(`🔍 사건 처리 시작: ${court} ${caseNumber} (${manager})`);
      
      // 새 사이트 접속
      cy.visit('https://www.scourt.go.kr/portal/information/events/search/search.jsp');
      cy.wait(8000); // WebSquare 로딩 대기
      
      cy.log('✅ 사이트 접속 완료');
      
      // 사건번호 파싱
      const [caseYear, caseSerialNumber] = caseNumber.match(/[0-9]+/g);
      const [caseType] = caseNumber.match(/([가-힣])+/g);
      
      cy.log(`📋 사건 정보: 년도=${caseYear}, 종류=${caseType}, 번호=${caseSerialNumber}, 법원=${court}`);
      
      // === 요소가 로딩될 때까지 대기 ===
      cy.log('🔍 WebSquare 요소들 로딩 대기 중...');
      
      // 추가 대기 및 요소 존재 확인 (더 긴 대기시간)
      cy.wait(8000);
      
      // 여러 가능한 선택자로 법원 드롭다운 찾기 (상단 검색바 제외)
      const courtSelectors = [
        '#mf_ssgoTopMainTab_contents_content1_body_sbx_cortCd',
        'select[title*="법원"]',
        'select[class*="w2selectbox"]',
        'select:not(#search_total):not(.searchSelect)'  // 상단 검색바 제외
      ];
      
      let courtFound = false;
      
      courtSelectors.forEach(selector => {
        cy.get('body').then($body => {
          if ($body.find(selector).length > 0 && !courtFound) {
            cy.log(`✅ 법원 선택 드롭다운 발견: ${selector}`);
            cy.get(selector).first().then($select => {
              cy.wrap($select).select(court, { force: true });
              cy.log(`📋 법원 선택 완료: ${court}`);
              courtFound = true;
            });
          }
        });
      });
      
      cy.wait(500);
      
      // 2. 사건번호입력모드 체크박스 찾기
      const checkboxSelectors = [
        '#mf_ssgoTopMainTab_contents_content1_body_cbx_chkSanoInputMode_input_0',
        'input[title*="사건번호입력모드"]',
        'input[type="checkbox"]'
      ];
      
      checkboxSelectors.forEach(selector => {
        cy.get('body').then($body => {
          if ($body.find(selector).length > 0) {
            cy.log(`☑️ 사건번호입력모드 체크박스 시도: ${selector}`);
            cy.get(selector).first().check({ force: true });
          }
        });
      });
      
      cy.wait(1000);
      
      // 3. 사건번호 입력 필드 찾기
      const serialSelectors = [
        '#mf_ssgoTopMainTab_contents_content1_body_ibx_csSerial',
        'input[title*="사건일련번호"]',
        'input[maxlength="7"]',
        'input[type="text"][class*="w100px"]'
      ];
      
      serialSelectors.forEach(selector => {
        cy.get('body').then($body => {
          if ($body.find(selector).length > 0) {
            cy.log(`📝 사건번호 입력 시도: ${selector}`);
            cy.get(selector).first().then($input => {
              cy.wrap($input).clear({ force: true });
              cy.wrap($input).type(caseSerialNumber, { force: true });
              cy.log(`✅ 사건번호 입력 완료: ${caseSerialNumber}`);
            });
          }
        });
      });
      
      cy.wait(500);
      
      // 4. 당사자명 입력 필드 찾기  
      const nameSelectors = [
        '#mf_ssgoTopMainTab_contents_content1_body_ibx_btprNm',
        'input[title*="당사자명"]',
        'input[placeholder*="당사자명"]',
        'input[maxlength="40"]'
      ];
      
      nameSelectors.forEach(selector => {
        cy.get('body').then($body => {
          if ($body.find(selector).length > 0) {
            cy.log(`👤 당사자명 입력 시도: ${selector}`);
            cy.get(selector).first().then($input => {
              cy.wrap($input).clear({ force: true });
              cy.wrap($input).type(manager, { force: true });
              cy.log(`✅ 당사자명 입력 완료: ${manager}`);
            });
          }
        });
      });
      
      cy.wait(1000);
      
      // 5. 캐차 자동 인식 및 입력 (원본 case-ing 프로젝트 방식)
      const captchaSelectors = [
        '#mf_ssgoTopMainTab_contents_content1_body_ibx_answer',
        'input[title*="자동입력"]',
        'input[placeholder*="자동입력"]',
        'input[maxlength="6"]'
      ];
      
      const captchaImageSelectors = [
        '#mf_ssgoTopMainTab_contents_content1_body_img_captcha',
        'img[src*="captcha"]',
        'img[alt*="자동입력방지"]'
      ];
      
      // 캐차 자동 인식 시스템 (최대 20번 재시도)
      function solveCaptcha(retryCount = 0) {
        if (retryCount >= 20) {
          cy.log('❌ 캐차 인식 20번 실패 - 수동 입력 필요');
          return;
        }
        
        cy.log(`🔍 캐차 인식 시도 ${retryCount + 1}/20`);
        
        // 캐차 이미지 찾기
        captchaImageSelectors.forEach(selector => {
          cy.get('body').then($body => {
            if ($body.find(selector).length > 0) {
              cy.log(`🖼️ 캐차 이미지 발견: ${selector}`);
              
              // 캐차 이미지를 Base64로 변환하여 Lambda API로 전송
              cy.get(selector).first().then($img => {
                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');
                const img = new Image();
                
                img.crossOrigin = 'anonymous';
                img.onload = function() {
                  canvas.width = img.width;
                  canvas.height = img.height;
                  ctx.drawImage(img, 0, 0);
                  const base64 = canvas.toDataURL().split(',')[1];
                  
                  // Lambda API로 캐차 예측 요청
                  cy.request({
                    method: 'POST',
                    url: `${LAMBDA_API_URL}/predict`,
                    body: { image: base64 },
                    headers: { 'content-type': 'application/json' }
                  }).then((response) => {
                    if (response.status === 200 && response.body.prediction) {
                      const predictedText = response.body.prediction;
                      cy.log(`🤖 캐차 예측 결과: ${predictedText}`);
                      
                      // 예측 결과를 입력 필드에 입력
                      captchaSelectors.forEach(inputSelector => {
                        cy.get('body').then($body => {
                          if ($body.find(inputSelector).length > 0) {
                            cy.get(inputSelector).first().then($input => {
                              cy.wrap($input).clear({ force: true });
                              cy.wrap($input).type(predictedText, { force: true });
                              cy.log(`✅ 캐차 입력 완료: ${predictedText}`);
                            });
                          }
                        });
                      });
                    } else {
                      cy.log('⚠️ 캐차 예측 실패 - 재시도');
                      solveCaptcha(retryCount + 1);
                    }
                  }).catch(() => {
                    cy.log('❌ 캐차 API 오류 - 재시도');
                    solveCaptcha(retryCount + 1);
                  });
                };
                
                img.src = $img.attr('src');
              });
            }
          });
        });
      }
      
      // 간단한 캐차 처리 (테스트용)
      cy.log('⚠️ 캐차 처리 건너뛰기 - 직접 입력 필요');
      cy.wait(3000); // 수동 입력 시간
      
      // 6. 검색 버튼 찾기
      const searchSelectors = [
        '#mf_ssgoTopMainTab_contents_content1_body_btn_srchCs',
        'input[value="검색"]',
        'button:contains("검색")',
        'input[type="button"][title*="검색"]'
      ];
      
      // 강력한 검색 버튼 찾기
      let searchClicked = false;
      
      searchSelectors.forEach(selector => {
        cy.get('body').then($body => {
          if ($body.find(selector).length > 0 && !searchClicked) {
            cy.log(`🔍 검색 버튼 발견: ${selector}`);
            cy.get(selector).first().then($btn => {
              cy.wrap($btn).click({ force: true });
              cy.log('✅ 검색 버튼 클릭 완료!');
              searchClicked = true;
            });
          }
        });
      });
      
      // 검색 버튼을 못 찾은 경우 강제로 Enter 키 입력
      cy.then(() => {
        if (!searchClicked) {
          cy.log('⚠️ 검색 버튼을 찾지 못함 - Enter 키로 검색 시도');
          cy.get('body').type('{enter}');
        }
      });
      
      cy.wait(5000); // 검색 결과 대기
      
      // 7. 결과 처리
      cy.get('body').then($body => {
        const pageText = $body.text();
        
        // 사건이 없는 경우들
        const noResultPatterns = [
          '사건이 존재하지 않습니다',
          '검색 결과가 없습니다',
          '조회된 내용이 없습니다',
          '해당하는 사건이 없습니다',
          '검색된 사건이 없습니다',
          '잘못된 자동입력방지문자',
          '자동입력방지문자를 확인'
        ];
        
        const hasNoResult = noResultPatterns.some(pattern => pageText.includes(pattern));
        
        if (hasNoResult) {
          cy.log('📋 검색 결과: 사건이 존재하지 않음 또는 캐차 오류');
          // 검색 결과 없음 - caseLookup에 저장
          caseLookup[rowIndex] = [court, caseNumber, manager, '', '', '사건이 존재하지 않습니다.'];
        } else {
          cy.log('🎯 검색 결과: 사건 발견! 스크린샷 촬영 중...');
          
          // 현재 날짜 생성 (dayjs 없이)
          const today = new Date().toISOString().split('T')[0];
          
          // 스크린샷 촬영
          const filename = `${caseNumber.replace(/[^\w]/g, '_')}`;
          cy.screenshot(filename, {
            onAfterScreenshot($el, props) {
              caseLookup[rowIndex] = [
                court, caseNumber, manager, 
                props.path, 
                props.name, 
                today
              ];
              // cy.log() 대신 console.log() 사용
              console.log(`📸 스크린샷 저장 완료: ${filename}`);
            }
          });
          
          // 스크린샷 후 Cypress 로그 추가
          cy.log(`📸 스크린샷 촬영 완료: ${filename}`);
        }
        
        // URL 확인
        cy.url().then(url => {
          cy.log(`📍 현재 URL: ${url}`);
        });
      });
      
      cy.log(`✅ ${caseNumber} 처리 완료\n`);
    // });  // forEach 주석 처리
    
    // 마지막에 전체 결과 요약
    cy.then(() => {
      cy.log('🎉 테스트 자동화 프로세스 완료!');
      cy.log('📊 처리 결과 요약:');
      
      const result = caseLookup[rowIndex];
      if (Array.isArray(result)) {
        cy.log(`   행 ${rowIndex}: ${result[5] || '성공'} - ${result[1]}`);
      } else if (result) {
        cy.log(`   행 ${rowIndex}: ${result}`);
      }
    });
  });

  // afterEach 제거 - 단순한 단일 테스트용
});

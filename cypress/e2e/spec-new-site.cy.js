// 새 사이트 (www.scourt.go.kr) 전용 case-ing 스크립트
const dayjs = require('dayjs');
const minMax = require('dayjs/plugin/minMax');
dayjs.extend(minMax);

const LAMBDA_API_URL = Cypress.env('CYPRESS_LAMBDA_API_URL');
const S3_BUCKET_URL = Cypress.env('CYPRESS_S3_BUCKET_URL');

describe('Case-ing 새 사이트 자동화', () => {
  let caseLookup = {};
  let doneCaseLookup = {};

  beforeEach(() => {
    cy.fixture('cases_chunk_0').then((cases) => {
      cases.forEach(([rowIndex, court, caseNumber, manager]) => {
        caseLookup[rowIndex] = null;
        
        cy.log(`🔍 사건 처리 시작: ${court} ${caseNumber} (${manager})`);
        
        // 새 사이트 접속
        cy.visit({
          url: 'https://www.scourt.go.kr/portal/information/events/search/search.jsp',
          headers: {
            'Accept-Language': 'ko,en;q=0.9,ko-KR;q=0.8,en-US;q=0.7'
          },
          retryOnStatusCodeFailure: true
        });

        // 충분한 로딩 대기 (WebSquare Framework)
        cy.wait(8000);
        
        // 페이지 로딩 확인
        cy.title().should('include', '사건검색');
        
        cy.log('✅ 새 사이트 접속 완료');
        
        // 실제 검색 폼 찾기 및 입력 시도
        cy.log('🔍 검색 폼 요소들 찾는 중...');
        
        // 사건번호 파싱
        const [caseYear, caseSerialNumber] = caseNumber.match(/[0-9]+/g);
        const [caseType] = caseNumber.match(/([가-힣])+/g);
        
        cy.log(`📋 사건 정보: 년도=${caseYear}, 종류=${caseType}, 번호=${caseSerialNumber}`);
        
        // === 새 사이트 전용 요소 찾기 및 입력 ===
        
        // 1. 모든 가능한 입력 필드들 시도
        const possibleInputs = [
          // 일반적인 이름들
          'input[name="caseNumber"]',
          'input[name="caseNo"]', 
          'input[name="case_number"]',
          'input[name="eventNumber"]',
          'input[name="saNumber"]',
          'input[name="sa_number"]',
          'input[id="caseNumber"]',
          'input[id="caseNo"]',
          'input[id="case_number"]',
          'input[id="eventNumber"]',
          'input[id="saNumber"]',
          'input[id="sa_number"]',
          // WebSquare 패턴들
          'input[id*="case"]',
          'input[id*="Case"]',
          'input[id*="sa"]',
          'input[id*="Sa"]',
          'input[name*="case"]',
          'input[name*="Case"]',
          'input[name*="sa"]',
          'input[name*="Sa"]',
          // 텍스트 입력 필드들
          'input[type="text"]',
          'input[placeholder*="사건"]',
          'input[placeholder*="번호"]'
        ];
        
        // 2. 검색 버튼들
        const possibleButtons = [
          'button:contains("검색")',
          'button:contains("조회")',
          'input[type="submit"]',
          'input[value*="검색"]',
          'input[value*="조회"]',
          'a:contains("검색")',
          'a:contains("조회")',
          '[onclick*="search"]',
          '[onclick*="Search"]',
          '[onclick*="submit"]'
        ];
        
        // 3. 실제 입력 시도
        let inputSuccess = false;
        let buttonSuccess = false;
        
        // 입력 필드 찾기 및 입력
        possibleInputs.forEach(selector => {
          cy.get('body').then($body => {
            if ($body.find(selector).length > 0 && !inputSuccess) {
              cy.log(`✅ 입력 필드 발견: ${selector}`);
              
              // 전체 사건번호 입력 시도
              cy.get(selector).first().then($input => {
                // 먼저 전체 사건번호로 시도
                cy.wrap($input).clear({ force: true });
                cy.wrap($input).type(caseNumber, { force: true });
                cy.log(`📝 전체 사건번호 입력: ${caseNumber}`);
                inputSuccess = true;
              });
            }
          });
        });
        
        cy.wait(1000);
        
        // 검색 버튼 클릭 시도
        possibleButtons.forEach(selector => {
          cy.get('body').then($body => {
            if ($body.find(selector).length > 0 && !buttonSuccess) {
              cy.log(`✅ 검색 버튼 발견: ${selector}`);
              cy.get(selector).first().click({ force: true });
              buttonSuccess = true;
            }
          });
        });
        
        cy.wait(5000); // 검색 결과 대기
        
        // === 결과 페이지 처리 ===
        
        // 결과 확인 및 처리
        cy.get('body').then($body => {
          const pageText = $body.text();
          
          // 사건이 존재하지 않는 경우들
          const noResultPatterns = [
            '사건이 존재하지 않습니다',
            '검색 결과가 없습니다',
            '조회된 내용이 없습니다',
            '해당하는 사건이 없습니다',
            '검색된 사건이 없습니다'
          ];
          
          const hasNoResult = noResultPatterns.some(pattern => pageText.includes(pattern));
          
          if (hasNoResult) {
            cy.log('📋 사건이 존재하지 않음');
            caseLookup[rowIndex] = [court, caseNumber, manager, '', '', '사건이 존재하지 않습니다.'];
          } else {
            cy.log('🎯 사건 발견! 상세 정보 확인 중...');
            
            // 스크린샷 촬영
            const filename = `${caseNumber}`;
            cy.screenshot(filename, {
              onAfterScreenshot($el, props) {
                // 기본 날짜 설정
                const today = dayjs().format('YYYY. MM. DD');
                caseLookup[rowIndex] = [
                  court, caseNumber, manager, props.path, props.name, today
                ];
                cy.log(`📸 스크린샷 저장: ${filename}`);
              }
            });
          }
        });
      });
    });
  });

  afterEach(() => {
    // 구글 시트 업데이트 로직 (기존과 동일)
    Object.keys(caseLookup).forEach((rowIndex) => {
      if (doneCaseLookup[rowIndex]) return;
      
      const today = dayjs().format('YYYY-MM-DD');
      const [court, caseNumber, manager, imgPath, filename, date] = caseLookup[rowIndex];
      
      if (!imgPath) {
        cy.log(`⚠️ ${caseNumber}: 스크린샷 없음`);
        return;
      }

      cy.log(`📋 구글 시트 업데이트: ${caseNumber}`);
      
      // S3 업로드 및 구글 시트 업데이트는 기존 로직 사용
      cy.readFile(imgPath, 'base64').then((base64String) => {
        const buffer = Cypress.Buffer.from(base64String, 'base64');
        
        cy.request({
          method: 'PUT',
          url: `${S3_BUCKET_URL}/${filename}.png`,
          body: buffer,
          headers: {
            'Content-Type': 'image/png',
          },
        }).then(() => {
          cy.log(`☁️ S3 업로드 완료: ${filename}.png`);
          
          // 구글 시트 업데이트
          const updateData = [court, caseNumber, manager, `${S3_BUCKET_URL}/${filename}.png`, date];
          
          cy.request({
            method: 'POST',
            url: `${LAMBDA_API_URL}/cases`,
            body: {
              rowIndex: parseInt(rowIndex),
              data: updateData
            }
          }).then(() => {
            cy.log(`✅ 구글 시트 업데이트 완료: 행 ${rowIndex}`);
            doneCaseLookup[rowIndex] = true;
          });
        });
      });
    });
  });
});

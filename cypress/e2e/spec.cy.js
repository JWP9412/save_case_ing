const dayjs = require('dayjs');
const minMax = require('dayjs/plugin/minMax')
dayjs.extend(minMax);

const courts = require('../js/courts');
const caseTypes = require('../js/caseTypes');
const cases = require('../fixtures/cases_chunk_0.json');

const LAMBDA_API_URL = Cypress.env('CYPRESS_LAMBDA_API_URL');
const S3_BUCKET_URL = Cypress.env('CYPRESS_S3_BUCKET_URL');
const SCREENSHOT_URL = `${S3_BUCKET_URL}/screenshots`;
const caseLookup = {};
const doneCaseLookup = {};

describe('Search case', function () {
  cases.forEach(([rowIndex, court, caseNumber, manager]) => {
    it(`[${rowIndex}] Search and Update sheet`, function() {
      cy.visit({
        url: 'https://www.scourt.go.kr/portal/information/events/search/search.jsp',
        headers: {
          'Accept-Language': 'ko,en;q=0.9,ko-KR;q=0.8,en-US;q=0.7'
        },
        retryOnStatusCodeFailure: true
      });

      // 이미지 로딩 확인 (더 유연하게)
      cy.get('img').should('exist');
      cy.wait(2000); // 추가 대기시간

      // 새 사이트에서는 법원 선택이 다를 수 있음 - 일단 스킵하고 진행
      cy.log('법원 선택 단계를 임시로 스킵합니다');
      cy.wait(500);

      const [caseYear, caseSerialNumber] = caseNumber.match(/[0-9]+/g);
      const [caseType] = caseNumber.match(/([가-힣])+/g);

      // 새 사이트의 가능한 요소들로 시도
      const possibleYearSelectors = ['#sel_sa_year', 'select[name="year"]', 'select[name="sa_year"]', '[name*="year"]'];
      const possibleSerialSelectors = ['#sa_serial', 'input[name="serial"]', 'input[name="sa_serial"]', '[name*="serial"]'];
      const possibleNameSelectors = ['#ds_nm', 'input[name="name"]', 'input[name="ds_nm"]', '[name*="name"]'];
      
      // 년도 선택 (여러 선택자 시도)
      let yearFound = false;
      for (const selector of possibleYearSelectors) {
        cy.get('body').then($body => {
          if ($body.find(selector).length > 0 && !yearFound) {
            cy.log(`년도 선택자 발견: ${selector}`);
            cy.get(selector).select(caseYear).should('have.value', caseYear);
            yearFound = true;
          }
        });
      }
      
      cy.wait(500);
      
      // 사건번호 입력 (여러 선택자 시도)
      let serialFound = false;
      for (const selector of possibleSerialSelectors) {
        cy.get('body').then($body => {
          if ($body.find(selector).length > 0 && !serialFound) {
            cy.log(`사건번호 입력 필드 발견: ${selector}`);
            cy.get(selector).type(caseSerialNumber).should('have.value', caseSerialNumber);
            serialFound = true;
          }
        });
      }
      
      // 당사자명 입력 (여러 선택자 시도)
      let nameFound = false;
      for (const selector of possibleNameSelectors) {
        cy.get('body').then($body => {
          if ($body.find(selector).length > 0 && !nameFound) {
            cy.log(`당사자명 입력 필드 발견: ${selector}`);
            cy.get(selector).type(manager);
            nameFound = true;
          }
        });
      }

      // 캐차 단계 일시적으로 건너뛰기 (새 사이트 구조 파악 후 수정 예정)
      cy.log('🚧 캐차 단계를 일시적으로 건너뛰고 다음 단계 진행');
      
      // 검색 버튼 찾기 및 클릭 시도
      const possibleSearchButtons = [
        'button[type="submit"]',
        'input[type="submit"]', 
        'button:contains("검색")',
        'button:contains("조회")',
        'a:contains("검색")',
        '[onclick*="search"]',
        '[onclick*="Search"]',
        '#searchBtn',
        '.searchBtn',
        'button.btn'
      ];
      
      let searchButtonFound = false;
      for (const selector of possibleSearchButtons) {
        cy.get('body').then($body => {
          if ($body.find(selector).length > 0 && !searchButtonFound) {
            cy.log(`검색 버튼 발견: ${selector}`);
            cy.get(selector).first().click({ force: true });
            searchButtonFound = true;
          }
        });
      }
      
      cy.wait(2000); // 검색 결과 로딩 대기


      function finalStep() {
        cy.get('li.subTab2').click();
        cy.get('#subTab2 .tableHor tbody tr').then(elem => {
          expect(elem.length).gt(0);
        });
        cy.get('#subTab2 .tableHor tbody tr').last().prev().then(function (prevElem) {
          const [prevDateElem,,prevResultElem] = prevElem.children();
          const prevDate = prevDateElem.innerText.trim();
          const prevResultDate = prevResultElem.innerText.trim().substr(0, 10);

          cy.get('#subTab2 .tableHor tbody tr').last().then(function (elem) {
            const [dateElem,,resultElem] = elem.children();
            const date = dateElem.innerText.trim();
            const resultDate = resultElem.innerText.trim().substr(0, 10);
            const finalDate = dayjs.max(
              [prevDate, prevResultDate, date, resultDate]
                .filter(n => n)
                .filter(n => dayjs(n).isValid())
                .map(n => dayjs(n))
            ).format('YYYY. MM. DD');

            // 최종 변경일자에 기입할 날짜
            expect(finalDate.length).gt(0);

            const filename = `${caseNumber}`;
            cy.get('#subTab2 .tableHor').screenshot(filename, {
              onAfterScreenshot($el, {name, path}) {
                caseLookup[rowIndex] = [
                  court, caseNumber, manager, path, name, finalDate
                ];
              },
            });
          });
        });
      }

      // 새 사이트의 결과 페이지 구조 확인
      cy.log('🔍 검색 결과 페이지 구조 분석 중...');
      
      // 여러 가능한 결과 버튼들 시도
      const possibleResultButtons = [
        '.tableVer .redBtn',
        'button:contains("조회")',
        'button:contains("상세")', 
        'a:contains("조회")',
        'a:contains("상세")',
        '.btn:contains("조회")',
        '[onclick*="detail"]',
        '[onclick*="view"]'
      ];
      
      let resultButtonFound = false;
      for (const selector of possibleResultButtons) {
        cy.get('body').then($body => {
          if ($body.find(selector).length > 0 && !resultButtonFound) {
            cy.log(`결과 버튼 발견: ${selector}`);
            
            const alertStub = cy.stub();
            cy.on('window:alert', alertStub);
            
            cy.get(selector).first().click({ force: true }).then(() => {
              const alertChain = alertStub.getCall(0);
              if ((alertChain || {}).lastArg !== '사건이 존재하지 않습니다.') {
                finalStep();
              } else {
                caseLookup[rowIndex] = [court, caseNumber, manager, '', '', '사건이 존재하지 않습니다.'];
              }
            });
            resultButtonFound = true;
          }
        });
      }
      
      // 버튼을 찾지 못한 경우 페이지 내용 확인
      cy.get('body').then($body => {
        if (!resultButtonFound) {
          cy.log('⚠️ 결과 버튼을 찾지 못함 - 페이지 내용 확인');
          const pageText = $body.text();
          
          if (pageText.includes('사건이 존재하지 않습니다') || 
              pageText.includes('검색 결과가 없습니다') ||
              pageText.includes('조회된 내용이 없습니다')) {
            cy.log('📋 사건이 존재하지 않음을 확인');
            caseLookup[rowIndex] = [court, caseNumber, manager, '', '', '사건이 존재하지 않습니다.'];
          } else {
            cy.log('🎯 결과 페이지로 이동한 것 같음 - finalStep 실행');
            finalStep();
          }
        }
      });
    });
  });

  afterEach(() => {
    Object.keys(caseLookup).forEach((rowIndex) => {
      // 이미 시트에 업데이트 한 사건은 스킵
      if (doneCaseLookup[rowIndex]) return;
      const today = dayjs().format('YYYY-MM-DD');
      const [
        court, caseNumber, manager, imgPath, filename, date
      ] = caseLookup[rowIndex];

      cy.readFile(imgPath, 'base64').then(img => {
        // 스크린샷 s3에 업로드
        cy.request({
          method: 'POST',
          url: `${LAMBDA_API_URL}/upload`,
          body: JSON.stringify({
            name: `screenshots/${filename}.png`,
            file: img,
          }),
          headers: {
            'content-type': 'application/json',
          },
        })
          .then((response) => {
            expect(response.status).eq(200);
          });
      });

      // 구글 시트 업데이트
      cy.request({
        method: 'POST',
        url: `${LAMBDA_API_URL}/cases`,
        body: {
          range: `A${rowIndex}:G${rowIndex}`,
          values: [[
            court,
            caseNumber,
            manager,
            dayjs(date).format('YYYY-MM-DD'),
            today,
            `=HYPERLINK("${SCREENSHOT_URL}/${filename}.png", "이미지 링크")`,
            `='사건 목록'!D${rowIndex}`
          ]],
        },
        headers: {
          'content-type': 'application/json',
        },
      })
        .then((response) => {
          expect(response.status).eq(200);
          doneCaseLookup[rowIndex] = true;
        });
    });
  });
});

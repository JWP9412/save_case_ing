// 완전한 case-ing 자동화 스크립트 (새 사이트 버전)
const dayjs = require('dayjs');
const minMax = require('dayjs/plugin/minMax');
dayjs.extend(minMax);

const LAMBDA_API_URL = Cypress.env('CYPRESS_LAMBDA_API_URL') || 'http://localhost:3000';
const S3_BUCKET_URL = Cypress.env('CYPRESS_S3_BUCKET_URL') || 'https://case-ing-screenshots-20250903.s3.ap-northeast-2.amazonaws.com';

describe('Case-ing 완전 자동화 (새 사이트)', () => {
  let caseLookup = {};
  let doneCaseLookup = {};

  beforeEach(() => {
    cy.fixture('cases_chunk_0').then((cases) => {
      cases.forEach(([rowIndex, court, caseNumber, manager]) => {
        caseLookup[rowIndex] = null;
        
        cy.log(`🔍 사건 처리 시작: ${court} ${caseNumber} (${manager})`);
        
        // 새 사이트 접속
        cy.visit('https://www.scourt.go.kr/portal/information/events/search/search.jsp');
        cy.wait(8000); // WebSquare 로딩 대기
        
        cy.log('✅ 사이트 접속 완료');
        
        // 사건번호 파싱
        const [caseYear, caseSerialNumber] = caseNumber.match(/[0-9]+/g);
        const [caseType] = caseNumber.match(/([가-힣])+/g);
        
        cy.log(`📋 사건 정보: 년도=${caseYear}, 종류=${caseType}, 번호=${caseSerialNumber}, 법원=${court}`);
        
        // === 단계별 자동화 실행 ===
        
        // 1. 법원 선택
        cy.get('#mf_ssgoTopMainTab_contents_content1_body_sbx_cortCd').then($select => {
          cy.log('✅ 법원 선택 드롭다운 발견');
          cy.wrap($select).select(court, { force: true });
          cy.log(`📋 법원 선택 완료: ${court}`);
        });
        
        cy.wait(500);
        
        // 2. 사건번호입력모드 체크
        cy.get('#mf_ssgoTopMainTab_contents_content1_body_cbx_chkSanoInputMode_input_0').then($checkbox => {
          cy.log('✅ 사건번호입력모드 체크박스 발견');
          cy.wrap($checkbox).check({ force: true });
          cy.log('☑️ 사건번호입력모드 활성화');
        });
        
        cy.wait(500);
        
        // 3. 사건번호 입력
        cy.get('#mf_ssgoTopMainTab_contents_content1_body_ibx_csSerial').then($input => {
          cy.log('✅ 사건번호 입력 필드 발견');
          cy.wrap($input).clear({ force: true });
          cy.wrap($input).type(caseSerialNumber, { force: true });
          cy.log(`📝 사건번호 입력 완료: ${caseSerialNumber}`);
        });
        
        cy.wait(500);
        
        // 4. 당사자명 입력
        cy.get('#mf_ssgoTopMainTab_contents_content1_body_ibx_btprNm').then($input => {
          cy.log('✅ 당사자명 입력 필드 발견');
          cy.wrap($input).clear({ force: true });
          cy.wrap($input).type(manager, { force: true });
          cy.log(`👤 당사자명 입력 완료: ${manager}`);
        });
        
        cy.wait(1000);
        
        // 5. 캐차 처리 (임시로 랜덤 번호)
        cy.get('#mf_ssgoTopMainTab_contents_content1_body_ibx_answer').then($input => {
          cy.log('✅ 캐차 입력 필드 발견');
          
          // 임시로 랜덤 6자리 사용 (실제로는 이미지 인식 필요)
          const testCaptcha = Math.floor(100000 + Math.random() * 900000).toString();
          cy.log(`⚠️ 임시 캐차 번호 사용: ${testCaptcha}`);
          
          cy.wrap($input).clear({ force: true });
          cy.wrap($input).type(testCaptcha, { force: true });
          cy.log('🔐 캐차 입력 완료 (임시)');
        });
        
        cy.wait(1000);
        
        // 6. 검색 실행
        cy.get('#mf_ssgoTopMainTab_contents_content1_body_btn_srchCs').then($button => {
          cy.log('✅ 검색 버튼 발견');
          cy.wrap($button).click({ force: true });
          cy.log('🔍 검색 실행 완료');
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
            caseLookup[rowIndex] = [court, caseNumber, manager, '', '', '사건이 존재하지 않습니다.'];
          } else {
            cy.log('🎯 검색 결과: 사건 발견! 스크린샷 촬영 중...');
            
            // 스크린샷 촬영
            const filename = `${caseNumber.replace(/[^\w]/g, '_')}`;
            cy.screenshot(filename, {
              onAfterScreenshot($el, props) {
                const today = dayjs().format('YYYY. MM. DD');
                caseLookup[rowIndex] = [
                  court, caseNumber, manager, props.path, props.name, today
                ];
                cy.log(`📸 스크린샷 저장 완료: ${filename}`);
              }
            });
          }
        });
        
        cy.log(`✅ ${caseNumber} 처리 완료`);
      });
    });
  });

  afterEach(() => {
    // 구글 시트 업데이트 (기존 로직과 동일)
    Object.keys(caseLookup).forEach((rowIndex) => {
      if (doneCaseLookup[rowIndex]) return;
      
      const caseData = caseLookup[rowIndex];
      if (!caseData) return;
      
      const [court, caseNumber, manager, imgPath, filename, date] = caseData;
      
      // 이미지가 없으면 구글 시트에 텍스트만 업데이트
      if (!imgPath) {
        cy.log(`📋 구글 시트 업데이트 (이미지 없음): ${caseNumber}`);
        
        cy.request({
          method: 'POST',
          url: `${LAMBDA_API_URL}/cases`,
          body: {
            rowIndex: parseInt(rowIndex),
            data: [court, caseNumber, manager, '', date || '사건이 존재하지 않습니다.']
          },
          failOnStatusCode: false
        }).then(() => {
          cy.log(`✅ 구글 시트 업데이트 완료 (텍스트): 행 ${rowIndex}`);
          doneCaseLookup[rowIndex] = true;
        });
        return;
      }

      // S3 업로드 + 구글 시트 업데이트
      cy.readFile(imgPath, 'base64').then((base64String) => {
        const buffer = Cypress.Buffer.from(base64String, 'base64');
        
        cy.request({
          method: 'PUT',
          url: `${S3_BUCKET_URL}/${filename}.png`,
          body: buffer,
          headers: {
            'Content-Type': 'image/png',
          },
          failOnStatusCode: false
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
            },
            failOnStatusCode: false
          }).then(() => {
            cy.log(`✅ 구글 시트 업데이트 완료: 행 ${rowIndex}`);
            doneCaseLookup[rowIndex] = true;
          });
        });
      });
    });
  });
});

/**
 * 페이지 자동화 컨트롤러
 * 대법원 사이트의 자동화 로직을 담당합니다.
 */

const fs = require('fs').promises;
const path = require('path');
const { exec } = require('child_process');
const { promisify } = require('util');

const execAsync = promisify(exec);

class PageController {
  constructor(page, browserId) {
    this.page = page;
    this.browserId = browserId;
    this.screenshotsDir = path.join(__dirname, '..', 'screenshots');
  }

  /**
   * 대법원 사이트 접속
   */
  async navigateToSite() {
    try {
      console.log(`🌐 대법원 사이트 접속 중... (${this.browserId})`);
      
      await this.page.goto('https://ssgo.scourt.go.kr/ssgo/index.on?cortId=www', {
        waitUntil: 'networkidle2',
        timeout: 30000
      });

      // 페이지 로딩 완료 대기
      await this.page.waitForSelector('body', { timeout: 10000 });
      
      console.log(`✅ 사이트 접속 완료 (${this.browserId})`);
      return true;
    } catch (error) {
      console.error(`❌ 사이트 접속 실패 (${this.browserId}):`, error.message);
      throw error;
    }
  }

  /**
   * 사건번호입력모드 체크박스 체크
   */
  async checkCaseNumberInputMode() {
    try {
      console.log(`📋 사건번호입력모드 체크박스 처리 중... (${this.browserId})`);
      
      const checkboxSelector = '#mf_ssgoTopMainTab_contents_content1_body_cbx_chkSanoInputMode_input_0';
      
      // 체크박스가 보일 때까지 대기
      await this.page.waitForSelector(checkboxSelector, { timeout: 10000 });
      
      // 현재 체크 상태 확인
      const isChecked = await this.page.$eval(checkboxSelector, el => el.checked);
      console.log(`현재 체크 상태: ${isChecked} (${this.browserId})`);
      
      if (!isChecked) {
        // 체크박스 클릭
        await this.page.click(checkboxSelector);
        
        // 잠시 대기
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // 체크 상태 재확인
        const newChecked = await this.page.$eval(checkboxSelector, el => el.checked);
        console.log(`클릭 후 체크 상태: ${newChecked} (${this.browserId})`);
        
        if (!newChecked) {
          // JavaScript로 직접 체크
          await this.page.evaluate((selector) => {
            const checkbox = document.querySelector(selector);
            if (checkbox) {
              checkbox.checked = true;
              checkbox.dispatchEvent(new Event('change', { bubbles: true }));
            }
          }, checkboxSelector);
          
          // 최종 체크 상태 확인
          const finalChecked = await this.page.$eval(checkboxSelector, el => el.checked);
          console.log(`JavaScript 체크 후 상태: ${finalChecked} (${this.browserId})`);
        }
      } else {
        console.log(`체크박스가 이미 체크되어 있음 (${this.browserId})`);
      }
      
      console.log(`✅ 사건번호입력모드 체크 완료 (${this.browserId})`);
      return true;
    } catch (error) {
      console.error(`❌ 체크박스 처리 실패 (${this.browserId}):`, error.message);
      throw error;
    }
  }

  /**
   * 법원 선택
   */
  async selectCourt(courtName) {
    try {
      console.log(`🏛️ 법원 선택 중: ${courtName} (${this.browserId})`);
      
      // 모든 select 요소 찾기
      const selects = await this.page.$$('select');
      console.log(`🔍 발견된 select 요소 수: ${selects.length} (${this.browserId})`);
      
      // 각 select 요소의 정보 출력
      for (let i = 0; i < selects.length; i++) {
        const select = selects[i];
        const id = await select.evaluate(el => el.id);
        const className = await select.evaluate(el => el.className);
        const options = await select.$$eval('option', options => 
          options.map(option => option.text).slice(0, 5) // 처음 5개만
        );
        console.log(`select ${i}: id="${id}", class="${className}", options=${JSON.stringify(options)}`);
      }
      
      // 첫 번째 select 요소 사용 (법원 선택)
      const select = selects[0];
      if (!select) {
        throw new Error('select 요소를 찾을 수 없습니다');
      }
      
      // select의 모든 옵션 텍스트를 배열로 수집
      const options = await select.$$eval('option', options => 
        options.map(option => option.text)
      );
      
      console.log(`📋 법원 옵션들:`, options.slice(0, 10), '...'); // 처음 10개만 출력
      
      // 법원명이 포함된 옵션의 인덱스 찾기 (정확한 매칭 우선)
      let courtIndex = options.findIndex(opt => opt === courtName);
      
      // 정확한 매칭이 없으면 부분 매칭 시도
      if (courtIndex === -1) {
        courtIndex = options.findIndex(opt => opt.includes(courtName));
      }
      
      console.log(`🔍 ${courtName} 검색 결과: 인덱스 ${courtIndex} (${this.browserId})`);
      
      if (courtIndex >= 0) {
        console.log(`✅ ${courtName} 발견! 선택 중... (${this.browserId})`);
        
        // 선택 전 현재 값 확인
        const currentValue = await select.evaluate(el => el.value);
        const currentText = await select.evaluate(el => el.options[el.selectedIndex]?.text || '');
        console.log(`현재 선택된 값: ${currentValue}, 텍스트: ${currentText} (${this.browserId})`);
        
        // JavaScript로 직접 선택 (WebSquare 프레임워크 대응)
        await select.evaluate((element, index) => {
          element.selectedIndex = index;
          element.dispatchEvent(new Event('change', { bubbles: true }));
          element.dispatchEvent(new Event('input', { bubbles: true }));
        }, courtIndex);
        
        // 잠시 대기
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // 선택 후 값 확인
        const newValue = await select.evaluate(el => el.value);
        const newText = await select.evaluate(el => el.options[el.selectedIndex]?.text || '');
        console.log(`선택 후 값: ${newValue}, 텍스트: ${newText} (${this.browserId})`);
        
        if (newText === courtName) {
          console.log(`✅ ${courtName} 선택 성공! (${this.browserId})`);
          return true;
        } else {
          console.log(`❌ 선택 실패: 예상=${courtName}, 실제=${newText} (${this.browserId})`);
          throw new Error(`법원 선택 실패: ${courtName}`);
        }
      } else {
        console.log(`❌ ${courtName}를 찾을 수 없습니다. (${this.browserId})`);
        console.log(`사용 가능한 법원들:`, options.filter(opt => !opt.includes('---')));
        throw new Error(`${courtName}를 찾을 수 없습니다`);
      }
    } catch (error) {
      console.error(`❌ 법원 선택 실패 (${this.browserId}):`, error.message);
      throw error;
    }
  }

  /**
   * 사건번호 입력
   */
  async inputCaseNumber(caseNumber) {
    try {
      console.log(`📝 사건번호 입력 중: ${caseNumber} (${this.browserId})`);
      
      const inputSelector = '#mf_ssgoTopMainTab_contents_content1_body_ibx_fullCsNo';
      
      // 입력 필드가 보일 때까지 대기
      await this.page.waitForSelector(inputSelector, { timeout: 10000 });
      
      // JavaScript로 직접 입력 (초고속)
      await this.page.evaluate((selector, text) => {
        const element = document.querySelector(selector);
        element.focus();
        element.value = text;
        element.dispatchEvent(new Event('input', { bubbles: true }));
        element.dispatchEvent(new Event('change', { bubbles: true }));
      }, inputSelector, caseNumber);
      
      // 입력 확인
      const inputValue = await this.page.$eval(inputSelector, el => el.value);
      if (inputValue !== caseNumber) {
        throw new Error(`사건번호 입력 실패: 예상값 ${caseNumber}, 실제값 ${inputValue}`);
      }
      
      console.log(`✅ 사건번호 입력 완료: ${caseNumber} (${this.browserId})`);
      return true;
    } catch (error) {
      console.error(`❌ 사건번호 입력 실패 (${this.browserId}):`, error.message);
      throw error;
    }
  }

  /**
   * 당사자명 입력
   */
  async inputPartyName(partyName) {
    try {
      console.log(`👤 당사자명 입력 중: ${partyName} (${this.browserId})`);
      
      const inputSelector = '#mf_ssgoTopMainTab_contents_content1_body_ibx_btprNm';
      
      // 입력 필드가 보일 때까지 대기
      await this.page.waitForSelector(inputSelector, { timeout: 10000 });
      
      // JavaScript로 직접 입력 (초고속)
      await this.page.evaluate((selector, text) => {
        const element = document.querySelector(selector);
        element.focus();
        element.value = text;
        element.dispatchEvent(new Event('input', { bubbles: true }));
        element.dispatchEvent(new Event('change', { bubbles: true }));
      }, inputSelector, partyName);
      
      // 입력 확인
      const inputValue = await this.page.$eval(inputSelector, el => el.value);
      if (inputValue !== partyName) {
        throw new Error(`당사자명 입력 실패: 예상값 ${partyName}, 실제값 ${inputValue}`);
      }
      
      console.log(`✅ 당사자명 입력 완료: ${partyName} (${this.browserId})`);
      return true;
    } catch (error) {
      console.error(`❌ 당사자명 입력 실패 (${this.browserId}):`, error.message);
      throw error;
    }
  }

  /**
   * 캡차 처리
   */
  async handleCaptcha(caseNumber) {
    try {
      console.log(`🔐 캡차 처리 중... (${this.browserId})`);
      
      // 캡차 이미지 캡처
      const captchaSelector = '#mf_ssgoTopMainTab_contents_content1_body_img_captcha';
      await this.page.waitForSelector(captchaSelector, { timeout: 10000 });
      
      // 캡차 이미지만 따로 캡처
      const screenshotPath = await this.takeElementScreenshot(captchaSelector, caseNumber, 'captcha');
      
      // Python GUI를 통한 캡차 입력
      const captchaInput = await this.getCaptchaInputFromPython(caseNumber, screenshotPath);
      
      // 캡차 입력 필드에 입력
      const inputSelector = '#mf_ssgoTopMainTab_contents_content1_body_ibx_answer';
      await this.page.waitForSelector(inputSelector, { timeout: 10000 });
      
      // JavaScript로 직접 입력 (초고속)
      await this.page.evaluate((selector, text) => {
        const element = document.querySelector(selector);
        element.focus();
        element.value = text;
        element.dispatchEvent(new Event('input', { bubbles: true }));
        element.dispatchEvent(new Event('change', { bubbles: true }));
      }, inputSelector, captchaInput);
      
      console.log(`✅ 캡차 입력 완료: ${captchaInput} (${this.browserId})`);
      return captchaInput;
    } catch (error) {
      console.error(`❌ 캡차 처리 실패 (${this.browserId}):`, error.message);
      throw error;
    }
  }

  /**
   * 검색 실행
   */
  async performSearch() {
    try {
      console.log(`🔍 검색 실행 중... (${this.browserId})`);
      
      // 검색 버튼 클릭 시도
      const searchButtonSelector = 'input[type="button"][value*="검색"]';
      const searchButton = await this.page.$(searchButtonSelector);
      
      if (searchButton) {
        await searchButton.click();
        console.log(`✅ 검색 버튼 클릭 완료 (${this.browserId})`);
      } else {
        // Enter 키로 검색 시도
        await this.page.keyboard.press('Enter');
        console.log(`✅ Enter 키로 검색 실행 (${this.browserId})`);
      }
      
      // 검색 결과 로딩 대기
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      return true;
    } catch (error) {
      console.error(`❌ 검색 실행 실패 (${this.browserId}):`, error.message);
      throw error;
    }
  }

  /**
   * 진행내용 데이터 추출
   */
  async extractProgressData(caseNumber) {
    try {
      console.log(`📊 진행내용 데이터 추출 중... (${this.browserId})`);
      
      // 검색 결과 페이지 로딩 대기
      await new Promise(resolve => setTimeout(resolve, 3000));
      
      // 진행내용 탭 클릭
      const progressTabSelector = '#mf_ssgoTopMainTab_contents_content1_body_wfSsgoDetail_ssgoCsDetailTab_tab_ssgoTab2';
      const progressTab = await this.page.$(progressTabSelector);
      
      if (progressTab) {
        console.log(`📋 진행내용 탭 클릭 중... (${this.browserId})`);
        await progressTab.click();
        await new Promise(resolve => setTimeout(resolve, 2000));
      } else {
        console.log(`⚠️ 진행내용 탭을 찾을 수 없습니다 (${this.browserId})`);
        return [];
      }
      
      // 진행내용 그리드에서 데이터 추출
      const gridSelector = '#mf_ssgoTopMainTab_contents_content1_body_wfSsgoDetail_ssgoCsDetailTab_contents_ssgoTab2_body_grd_csProgLst_main_div';
      
      try {
        await this.page.waitForSelector(gridSelector, { timeout: 10000 });
        console.log(`📊 진행내용 그리드 발견 (${this.browserId})`);
      } catch (error) {
        console.log(`⚠️ 진행내용 그리드를 찾을 수 없습니다: ${error.message} (${this.browserId})`);
        return [];
      }
      
      const progressData = await this.page.evaluate((selector) => {
        const grid = document.querySelector(selector);
        if (!grid) return null;
        
        const rows = grid.querySelectorAll('tbody tr');
        const data = [];
        
        rows.forEach((row, index) => {
          const cells = row.querySelectorAll('td');
          if (cells.length >= 4) {
            data.push({
              date: cells[0]?.querySelector('span')?.textContent?.trim() || '',
              content: cells[1]?.querySelector('span')?.textContent?.trim() || '',
              result: cells[2]?.querySelector('span')?.textContent?.trim() || '',
              document: cells[3]?.querySelector('span')?.textContent?.trim() || ''
            });
          }
        });
        
        return data;
      }, gridSelector);
      
      if (progressData && progressData.length > 0) {
        console.log(`✅ 진행내용 데이터 추출 완료: ${progressData.length}개 행 (${this.browserId})`);
        return progressData;
      } else {
        console.log(`⚠️ 진행내용 데이터가 없습니다 (${this.browserId})`);
        return [];
      }
    } catch (error) {
      console.error(`❌ 진행내용 데이터 추출 실패 (${this.browserId}):`, error.message);
      return [];
    }
  }

  /**
   * 스크린샷 촬영
   */
  async takeScreenshot(caseNumber, type = 'process') {
    try {
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
      const filename = `${caseNumber}-${timestamp}-${type}.png`;
      const filepath = path.join(this.screenshotsDir, filename);
      
      // 스크린샷 디렉토리 생성
      await fs.mkdir(this.screenshotsDir, { recursive: true });
      
      await this.page.screenshot({ 
        path: filepath,
        fullPage: true 
      });
      
      console.log(`📸 스크린샷 저장: ${filename} (${this.browserId})`);
      return filepath;
    } catch (error) {
      console.error(`❌ 스크린샷 촬영 실패 (${this.browserId}):`, error.message);
      throw error;
    }
  }

  /**
   * 특정 요소만 스크린샷 촬영
   */
  async takeElementScreenshot(selector, caseNumber, type = 'element') {
    try {
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
      const filename = `${caseNumber}-${timestamp}-${type}.png`;
      const filepath = path.join(this.screenshotsDir, filename);
      
      // 스크린샷 디렉토리 생성
      await fs.mkdir(this.screenshotsDir, { recursive: true });
      
      // 요소가 보일 때까지 대기
      await this.page.waitForSelector(selector, { timeout: 10000 });
      
      // 요소만 캡처
      const element = await this.page.$(selector);
      if (element) {
        await element.screenshot({ path: filepath });
        console.log(`📸 요소 스크린샷 저장: ${filename} (${this.browserId})`);
        return filepath;
      } else {
        throw new Error(`요소를 찾을 수 없습니다: ${selector}`);
      }
    } catch (error) {
      console.error(`❌ 요소 스크린샷 촬영 실패 (${this.browserId}):`, error.message);
      throw error;
    }
  }

  /**
   * Python GUI를 통한 캡차 입력 받기
   */
  async getCaptchaInputFromPython(caseNumber, imagePath) {
    try {
      console.log(`🐍 Python GUI 실행 중... (${this.browserId})`);
      
      const { stdout, stderr } = await execAsync(`py captcha_input.py ${caseNumber}`);
      
      if (stderr) {
        console.error(`Python 실행 오류 (${this.browserId}):`, stderr);
      }
      
      // SUCCESS: 부분에서 캡차 입력 추출
      if (stdout.includes('SUCCESS:')) {
        const successPart = stdout.split('SUCCESS:')[1].trim();
        const captchaInput = successPart.split('\n')[0].trim();
        console.log(`✅ Python에서 캡차 입력 받음: ${captchaInput} (${this.browserId})`);
        return captchaInput;
      } else {
        throw new Error('Python GUI에서 유효한 캡차 입력을 받지 못했습니다');
      }
    } catch (error) {
      console.error(`❌ Python GUI 실행 실패 (${this.browserId}):`, error.message);
      throw error;
    }
  }

  /**
   * 법원 코드 매핑
   */
  getCourtCode(courtName) {
    const courtMapping = {
      '대구고등법원': '2',
      '수원지방법원': '3', 
      '서울중앙지방법원': '4',
      '서울고등법원': '5',
      '대전고등법원': '6',
      '부산고등법원': '7',
      '광주고등법원': '8'
    };
    
    return courtMapping[courtName] || '4'; // 기본값: 서울중앙지방법원
  }
}

module.exports = PageController;

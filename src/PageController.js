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
    // 진행내용 탭 클릭 전에 읽은 일반내용 (없으면 null)
    this.lastGeneralInfo = null;
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

        // 체크 상태가 될 때까지 스마트 대기 (최대 3초, 보통 0.1초 내 완료)
        try {
          await this.page.waitForFunction(
            (selector) => document.querySelector(selector) && document.querySelector(selector).checked === true,
            { timeout: 3000 },
            checkboxSelector
          );
        } catch (e) {
          // 타임아웃 시 아래 재확인 로직으로 진행
        }

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
   * 사건검색 결과 저장 체크박스 체크 (검증된 방식 적용)
   */
  async checkSaveSearchResult() {
    try {
      console.log(`💾 사건검색 결과 저장 체크박스 처리 중... (${this.browserId})`);

      const checkboxSelector = '#mf_ssgoTopMainTab_contents_content1_body_cbx_saveCsRsltYn_input_0';

      // 체크박스가 보일 때까지 대기
      await this.page.waitForSelector(checkboxSelector, { timeout: 10000 });

      // 현재 체크 상태 확인
      const isChecked = await this.page.$eval(checkboxSelector, el => el.checked);
      console.log(`현재 '결과 저장' 체크 상태: ${isChecked} (${this.browserId})`);

      if (!isChecked) {
        // 체크박스 클릭
        await this.page.click(checkboxSelector);

        // 체크 상태가 될 때까지 스마트 대기 (최대 3초)
        try {
          await this.page.waitForFunction(
            (selector) => document.querySelector(selector) && document.querySelector(selector).checked === true,
            { timeout: 3000 },
            checkboxSelector
          );
        } catch (e) {
          // 타임아웃 시 아래 재확인 로직으로 진행
        }

        // 체크 상태 재확인
        const newChecked = await this.page.$eval(checkboxSelector, el => el.checked);
        console.log(`클릭 후 '결과 저장' 체크 상태: ${newChecked} (${this.browserId})`);

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
          console.log(`JavaScript 체크 후 '결과 저장' 상태: ${finalChecked} (${this.browserId})`);
        }
      } else {
        console.log(`'결과 저장'이 이미 체크되어 있음 (${this.browserId})`);
      }

      console.log(`✅ 사건검색 결과 저장 체크 완료 (${this.browserId})`);
      return true;
    } catch (error) {
      console.error(`❌ '결과 저장' 체크박스 처리 실패 (${this.browserId}):`, error.message);
      // 체크박스 실패는 치명적이지 않으므로 에러를 던지지 않고 진행 (선택사항)
      return false;
    }
  }

  /**
   * 법원 선택
   */
  async selectCourt(courtName) {
    try {
      console.log(`🏛️ 법원 선택 중: ${courtName} (${this.browserId})`);

      // select 요소가 로드될 때까지 대기 (최대 15초)
      await this.page.waitForSelector('select', { timeout: 15000 });

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

        // 선택된 값이 반영될 때까지 스마트 대기 (최대 5초)
        try {
          await this.page.waitForFunction(
            (expectedText) => {
              const sel = document.querySelector('select');
              return sel && sel.options[sel.selectedIndex] && sel.options[sel.selectedIndex].text === expectedText;
            },
            { timeout: 5000 },
            courtName
          );
        } catch (e) {
          // 타임아웃 시 아래 검증으로 진행
        }

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
    this.caseNumber = caseNumber; // [SMART SKIP] 사건번호 저장
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
   * 캡차 입력 (간단한 버전)
   */
  async inputCaptcha(captchaInput) {
    if (captchaInput === "CLICK") {
      console.log(`⚡ [SMART SKIP] 캡차 입력 건너뜀 (${this.browserId})`);
      return;
    }
    try {
      console.log(`🔐 [DEBUG] 캡차 입력 시작 (${this.browserId})`);
      console.log(`📋 [DEBUG] 입력할 캡차 값: "${captchaInput}" (타입: ${typeof captchaInput}, 길이: ${captchaInput?.length})`);

      const captchaSelector = '#mf_ssgoTopMainTab_contents_content1_body_ibx_answer';
      console.log(`🔍 [DEBUG] 캡차 입력 필드 대기 중: ${captchaSelector}`);
      await this.page.waitForSelector(captchaSelector, { timeout: 10000 });
      console.log(`✅ [DEBUG] 캡차 입력 필드 찾음`);

      // 캡차 입력 필드 클리어 후 입력
      console.log(`🗑️ [DEBUG] 캡차 입력 필드 초기화 중...`);
      await this.page.evaluate((selector) => {
        const input = document.querySelector(selector);
        if (input) {
          input.value = '';
          input.focus();
        }
      }, captchaSelector);

      console.log(`⌨️ [DEBUG] 캡차 입력 중: "${captchaInput}"`);
      await this.page.type(captchaSelector, captchaInput, { delay: 10 });

      // 입력 후 실제로 입력된 값 확인
      const actualValue = await this.page.evaluate((selector) => {
        const input = document.querySelector(selector);
        return input ? input.value : null;
      }, captchaSelector);

      console.log(`🔍 [DEBUG] 입력 후 실제 값: "${actualValue}"`);
      console.log(`🔍 [DEBUG] 입력 값 일치: ${actualValue === captchaInput}`);

      if (actualValue !== captchaInput) {
        console.error(`⚠️ [경고] 캡차 입력 불일치! 예상: "${captchaInput}", 실제: "${actualValue}"`);
      }

      console.log(`✅ 캡차 입력 완료: ${captchaInput} (${this.browserId})`);
      return true;
    } catch (error) {
      console.error(`❌ 캡차 입력 실패 (${this.browserId}):`, error.message);
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
   * 대화형 캡차 처리 (사용자 입력 대기)
   */
  async handleInteractiveCaptcha(caseNumber) {
    try {
      console.log(`🔐 대화형 캡차 처리 중... (${this.browserId})`);

      // 캡차 이미지 캡처
      const captchaSelector = '#mf_ssgoTopMainTab_contents_content1_body_img_captcha';
      await this.page.waitForSelector(captchaSelector, { timeout: 10000 });

      // 캡차 이미지만 따로 캡처
      const screenshotPath = await this.takeElementScreenshot(captchaSelector, caseNumber, 'captcha');

      console.log(`📸 캡차 이미지 캡처 완료: ${screenshotPath}`);
      console.log(`⏳ 사용자가 캡차를 입력할 때까지 대기 중...`);
      console.log(`💡 브라우저 창에서 캡차를 확인하고 직접 입력하세요.`);

      // 캡차 입력 필드 선택자
      const inputSelector = '#mf_ssgoTopMainTab_contents_content1_body_ibx_answer';
      await this.page.waitForSelector(inputSelector, { timeout: 10000 });

      // 사용자가 캡차를 입력할 때까지 대기 (최대 5분)
      const maxWaitTime = 300000; // 5분
      const checkInterval = 1000; // 1초마다 확인
      let waitTime = 0;

      while (waitTime < maxWaitTime) {
        const captchaInput = await this.page.$eval(inputSelector, el => el.value);

        if (captchaInput && captchaInput.trim()) {
          console.log(`✅ 캡차 입력 완료: ${captchaInput} (${this.browserId})`);
          return captchaInput.trim();
        }

        // 1초 대기
        await new Promise(resolve => setTimeout(resolve, checkInterval));
        waitTime += checkInterval;

        // 10초마다 상태 출력
        if (waitTime % 10000 === 0) {
          console.log(`⏳ 캡차 입력 대기 중... (${Math.floor(waitTime / 1000)}초 경과)`);
        }
      }

      throw new Error('캡차 입력 시간 초과 (5분)');
    } catch (error) {
      console.error(`❌ 대화형 캡차 처리 실패 (${this.browserId}):`, error.message);
      throw error;
    }
  }

  /**
   * 최근 검색 결과 클릭 (캡차 스킵용)
   */
  async clickRecentCase(caseNumber) {
    try {
      console.log(`🖱️ [SMART SKIP] 최근 검색 결과 클릭 시도: ${caseNumber} (${this.browserId})`);

      const clicked = await this.page.evaluate((targetNo) => {
        const elements = document.querySelectorAll('a');
        for (const el of elements) {
          if (el.textContent.trim() === targetNo) {
            el.click();
            return true;
          }
        }
        return false;
      }, caseNumber);

      if (clicked) {
        console.log(`✅ [SMART SKIP] 최근 검색 결과 클릭 성공 (${this.browserId})`);

        // 클릭 후 로딩 대기
        await new Promise(resolve => setTimeout(resolve, 2000));
        return true;
      } else {
        throw new Error(`최근 검색 목록에서 사건번호(${caseNumber})를 찾을 수 없습니다.`);
      }
    } catch (error) {
      console.error(`❌ [SMART SKIP] 클릭 실패 (${this.browserId}):`, error.message);
      throw error;
    }
  }

  /**
   * 검색 실행
   */
  async performSearch(captchaInput) {
    try {
      // [SMART SKIP] "CLICK" 신호 처리
      if (captchaInput === "CLICK") {
        console.log(`⚡ [SMART SKIP] 검색 버튼 클릭 대신 링크 클릭 모드 진입 (${this.browserId})`);
        return await this.clickRecentCase(this.caseNumber);
      }

      console.log(`🔍 검색 실행 중... (${this.browserId})`);

      // 검색 버튼 클릭 시도
      const searchButtonSelector = 'input[type="button"][value*="검색"]';
      const searchButton = await this.page.$(searchButtonSelector);

      // [CRITICAL FIX] 사건번호 인식 문제 해결을 위한 재클릭 및 포커스
      try {
        console.log(`🖱️ [DEBUG] 사건번호 입력 필드 재확인 (Focus & Click)`);
        const caseNoSelector = '#mf_ssgoTopMainTab_contents_content1_body_ibx_fullCsNo';
        await this.page.evaluate((selector) => {
          const input = document.querySelector(selector);
          if (input) {
            input.click(); // 클릭
            input.focus(); // 포커스
            input.dispatchEvent(new Event('input', { bubbles: true })); // 입력 이벤트
            input.dispatchEvent(new Event('change', { bubbles: true })); // 변경 이벤트
          }
        }, caseNoSelector);

        console.log(`🖱️ [DEBUG] 당사자명 입력 필드 재확인 (Focus & Click)`);
        const partyNameSelector = '#mf_ssgoTopMainTab_contents_content1_body_ibx_btprNm';
        await this.page.evaluate((selector) => {
          const input = document.querySelector(selector);
          if (input) {
            input.click(); // 클릭
            input.focus(); // 포커스
            input.dispatchEvent(new Event('input', { bubbles: true })); // 입력 이벤트
            input.dispatchEvent(new Event('change', { bubbles: true })); // 변경 이벤트
          }
        }, partyNameSelector);
      } catch (e) {
        console.log(`⚠️ 입력 필드 재클릭 실패 (무시됨): ${e.message}`);
      }

      if (searchButton) {
        // [SIMPLIFY] Enter 키 입력 로직 제거 & 오직 클릭만 수행
        // Puppeteer click 대신 JS click 우선 사용 (WebSquare 이벤트 핸들링 보장)
        console.log(`🖱️ [DEBUG] 검색 버튼 클릭 시도 (JS Click)`);
        
        await this.page.evaluate((selector) => {
          const btn = document.querySelector(selector);
          if (btn) {
            btn.click();
          }
        }, searchButtonSelector);

        console.log(`✅ 검색 버튼 클릭 완료 (${this.browserId})`);
      } else {
        console.warn(`⚠️ 검색 버튼을 찾을 수 없습니다. Enter 키로 대체 시도.`);
        await this.page.keyboard.press('Enter');
      }

      // 검색 결과는 다음 단계(extractProgressData)에서 그리드 waitForSelector로 대기하므로 고정 대기 제거
      return true;
    } catch (error) {
      console.error(`❌ 검색 실행 실패 (${this.browserId}):`, error.message);
      throw error;
    }
  }

  /**
   * 검색 결과 목록 페이지에서 해당 사건번호 링크를 클릭해 상세 페이지로 진입
   * (수동 캡차 입력 후 목록이 뜨는 경우 진행내용 탭이 없으므로 상세로 한 번 들어감)
   */
  async ensureDetailPageFromList(caseNumber) {
    if (!caseNumber) return false;
    try {
      const clicked = await this.page.evaluate((num) => {
        const links = document.querySelectorAll('a[href*="ssgo"], a[href*="csNo"], a');
        for (const a of links) {
          if (a.textContent && a.textContent.trim().indexOf(num) !== -1) {
            a.click();
            return true;
          }
        }
        const cells = document.querySelectorAll('td, span, div');
        for (const el of cells) {
          if (el.textContent && el.textContent.trim() === num && el.offsetParent !== null) {
            const parent = el.closest('a') || el.closest('tr');
            if (parent) {
              (parent.click ? parent : el).click();
              return true;
            }
          }
        }
        return false;
      }, caseNumber);
      if (clicked) {
        console.log(`✅ [LIST→DETAIL] 사건번호 링크 클릭: ${caseNumber} (${this.browserId})`);
        await new Promise((r) => setTimeout(r, 2000));
        return true;
      }
    } catch (e) {
      console.log(`⚠️ [LIST→DETAIL] 목록에서 링크 클릭 실패: ${e.message} (${this.browserId})`);
    }
    return false;
  }

  /**
   * 일반내용(기본내용·최근기일·최근제출서류·당사자·대리인) 추출
   * ----------------------------------------------------------
   * 진행내용 탭을 누르기 전 상세 페이지 DOM에서 읽습니다.
   * 실패해도 null만 반환하고, 진행내용 크롤링을 절대 막지 않습니다.
   *
   * 파싱 전략 (주니어 참고):
   * - WebSquare ID(ssgoTab1_body)가 있으면 그 안을 우선 스코프로 씁니다.
   * - 표는 ID보다 제목 텍스트("기본내용", "최근기일" 등)로 찾습니다.
   *   사이트 개편으로 ID가 바뀌어도 제목은 잘 안 바뀌기 때문입니다.
   */
  async extractGeneralInfo(caseNumber) {
    try {
      // 일반내용 영역이 보일 때까지 짧게 대기 (없어도 계속)
      try {
        await this.page.waitForFunction(() => {
          const bodyText = document.body ? document.body.innerText : '';
          return bodyText.includes('기본내용') || bodyText.includes('사건번호') ||
            !!document.querySelector('[id*="ssgoTab1_body"]');
        }, { timeout: 5000 });
      } catch (e) {
        console.log(`⚠️ [일반내용] 로딩 대기 타임아웃 (계속 시도)`);
      }

      const data = await this.page.evaluate(() => {
        function clean(t) {
          return (t || '').replace(/\s+/g, ' ').trim();
        }

        // 스코프: 일반내용 탭 body 우선, 없으면 상세 영역 전체
        const scope =
          document.querySelector(
            '#mf_ssgoTopMainTab_contents_content1_body_wfSsgoDetail_ssgoCsDetailTab_contents_ssgoTab1_body'
          ) ||
          document.querySelector('[id*="ssgoTab1_body"]') ||
          document.querySelector('[id*="wfSsgoDetail"]') ||
          document.body;

        /**
         * 라벨-값 표 파싱 (기본내용용)
         * 한 행이 [라벨, 값, 라벨, 값] 형태로 이어지는 경우가 많음
         */
        function parseLabelValueTable(table) {
          const result = {};
          if (!table) return result;
          const rows = table.querySelectorAll('tr');
          for (const tr of rows) {
            const cells = Array.from(tr.querySelectorAll('th, td'));
            // th/td 짝: 라벨 칸은 보통 짧고, 값 칸이 옆에 붙음
            let i = 0;
            while (i < cells.length) {
              const label = clean(cells[i].textContent);
              // 라벨처럼 보이는 칸만 (너무 긴 문장은 값으로 취급)
              if (label && label.length > 0 && label.length < 40 && i + 1 < cells.length) {
                const value = clean(cells[i + 1].textContent);
                // 이미 같은 키가 있으면 덮지 않음 (첫 값 우선)
                if (!(label in result)) {
                  result[label] = value;
                }
                i += 2;
              } else {
                i += 1;
              }
            }
          }
          return result;
        }

        /**
         * 헤더+데이터 행 표 파싱
         */
        function parseDataTable(table) {
          if (!table) return [];
          const rows = Array.from(table.querySelectorAll('tr'));
          if (rows.length === 0) return [];

          // 첫 행이 th를 포함하면 헤더, 아니면 첫 행을 헤더로 간주
          let headerRowIdx = 0;
          for (let r = 0; r < Math.min(rows.length, 3); r++) {
            if (rows[r].querySelector('th')) {
              headerRowIdx = r;
              break;
            }
          }
          const headers = Array.from(rows[headerRowIdx].querySelectorAll('th, td')).map((c) =>
            clean(c.textContent)
          );
          const data = [];
          for (let r = headerRowIdx + 1; r < rows.length; r++) {
            const cells = Array.from(rows[r].querySelectorAll('td, th')).map((c) =>
              clean(c.textContent)
            );
            if (cells.length === 0) continue;
            const joined = cells.join('');
            // "지정된 기일내용이 없습니다" 같은 안내 행은 스킵
            if (joined.includes('없습니다') || joined.includes('조회된 내용이 없')) {
              continue;
            }
            // 전부 빈 칸이면 스킵
            if (!joined.trim()) continue;
            const obj = {};
            headers.forEach((h, i) => {
              obj[h || `col${i}`] = cells[i] || '';
            });
            data.push(obj);
          }
          return data;
        }

        /**
         * 제목 텍스트 근처의 table을 찾음
         * titleSubstr: "최근기일", "제출서류", "당사자내용", "대리인내용" 등
         */
        function findTableNearTitle(titleSubstr) {
          const candidates = scope.querySelectorAll(
            'td, th, div, span, strong, b, legend, p, a, li, label'
          );
          for (const el of candidates) {
            // 자식이 많은 컨테이너의 전체 텍스트는 제목이 아님 → 짧은 텍스트만
            const ownText = clean(el.childNodes.length
              ? Array.from(el.childNodes)
                  .filter((n) => n.nodeType === 3)
                  .map((n) => n.textContent)
                  .join('')
              : el.textContent);
            const t = ownText || clean(el.textContent);
            if (!t || t.length > titleSubstr.length + 20) continue;
            if (!t.includes(titleSubstr)) continue;

            // 1) 같은 조상 안에서 뒤따르는 table
            let search = el;
            for (let up = 0; up < 6 && search; up++) {
              let sib = search.nextElementSibling;
              while (sib) {
                if (sib.tagName === 'TABLE') return sib;
                const nested = sib.querySelector && sib.querySelector('table');
                if (nested) return nested;
                sib = sib.nextElementSibling;
              }
              // 부모 안에서 el 다음에 오는 table
              if (search.parentElement) {
                const tables = search.parentElement.querySelectorAll('table');
                for (const tb of tables) {
                  // 제목 요소보다 뒤에 있는 표만
                  if (
                    el.compareDocumentPosition(tb) & Node.DOCUMENT_POSITION_FOLLOWING
                  ) {
                    return tb;
                  }
                }
              }
              search = search.parentElement;
            }
          }

          // 2) fallback: 표 앞쪽 텍스트에 제목이 포함된 경우
          for (const table of scope.querySelectorAll('table')) {
            let prev = table.previousElementSibling;
            for (let i = 0; i < 3 && prev; i++) {
              if (clean(prev.textContent).includes(titleSubstr)) return table;
              prev = prev.previousElementSibling;
            }
          }
          return null;
        }

        // --- 기본내용: '사건번호'와 '사건명'이 같이 있는 표 ---
        let basic = {};
        for (const table of scope.querySelectorAll('table')) {
          const text = table.textContent || '';
          if (text.includes('사건번호') && (text.includes('사건명') || text.includes('원고'))) {
            basic = parseLabelValueTable(table);
            if (Object.keys(basic).length >= 2) break;
          }
        }

        return {
          basic,
          recent_hearings: parseDataTable(findTableNearTitle('최근기일')),
          recent_documents: parseDataTable(findTableNearTitle('제출서류')),
          parties: parseDataTable(findTableNearTitle('당사자내용')),
          attorneys: parseDataTable(findTableNearTitle('대리인내용')),
        };
      });

      // 최소한 basic에 뭔가 있거나 표가 하나라도 있으면 성공으로 간주
      const hasAny =
        data &&
        ((data.basic && Object.keys(data.basic).length > 0) ||
          (data.recent_hearings && data.recent_hearings.length > 0) ||
          (data.recent_documents && data.recent_documents.length > 0) ||
          (data.parties && data.parties.length > 0) ||
          (data.attorneys && data.attorneys.length > 0));

      if (!hasAny) {
        console.log(`⚠️ [일반내용] 파싱 결과 비어 있음 (${caseNumber})`);
        return null;
      }

      console.log(
        `📊 [일반내용] basic=${Object.keys(data.basic || {}).length}키, ` +
          `기일=${(data.recent_hearings || []).length}, ` +
          `서류=${(data.recent_documents || []).length}, ` +
          `당사자=${(data.parties || []).length}, ` +
          `대리인=${(data.attorneys || []).length}`
      );
      return data;
    } catch (error) {
      console.error(`❌ [일반내용] 추출 실패: ${error.message}`);
      return null;
    }
  }

  /**
   * 진행내용 데이터 추출
   */
  async extractProgressData(caseNumber) {
    try {
      console.log(`⏳ [DEBUG] 검색 결과 로딩 대기 중... (${this.browserId})`);
      
      // 0. 검색 결과 대기 (상세 페이지 탭 또는 목록 그리드가 나타날 때까지)
      try {
        await this.page.waitForFunction(() => {
          const detailTab = document.querySelector('#mf_ssgoTopMainTab_contents_content1_body_wfSsgoDetail_ssgoCsDetailTab_tab_ssgoTab2');
          // 목록 그리드의 경우 일반적인 그리드 클래스나 링크 확인
          const listLinks = document.querySelectorAll('a[href*="ssgo"]'); 
          const gridBody = document.querySelector('.w2grid_body');
          return detailTab || (listLinks.length > 0) || gridBody;
        }, { timeout: 10000 });
      } catch (e) {
        console.log(`⚠️ [DEBUG] 검색 결과 로딩 대기 타임아웃 (계속 진행)`);
      }

      // 0.1 검색 결과 목록 페이지면 상세 페이지로 진입 (수동 캡차 후 목록이 뜬 경우)
      const progressTabSelector = '#mf_ssgoTopMainTab_contents_content1_body_wfSsgoDetail_ssgoCsDetailTab_tab_ssgoTab2';
      const hasProgressTab = await this.page.$(progressTabSelector);
      
      if (!hasProgressTab) {
        console.log(`ℹ️ [DEBUG] 진행내용 탭이 없음 -> 목록 페이지로 추정, 상세 진입 시도`);
        const wentToDetail = await this.ensureDetailPageFromList(caseNumber);
        if (wentToDetail) {
          console.log(`✅ [DEBUG] 상세 페이지 진입 성공, 탭 로딩 대기`);
          // 탭이 나타날 때까지 명시적 대기
          try {
            await this.page.waitForSelector(progressTabSelector, { timeout: 5000 });
          } catch (e) {
            console.log(`⚠️ [DEBUG] 상세 진입 후에도 탭이 안 보임`);
          }
        } else {
            console.log(`⚠️ [DEBUG] 목록에서 사건을 찾을 수 없거나 이미 상세 페이지일 수 있음`);
        }
      }

      // ★ 일반내용 추출: 진행내용 탭을 누르기 전 화면에 이미 떠 있는 표들을 읽습니다.
      // 실패해도 진행내용 크롤링은 계속되어야 하므로 내부에서 예외를 삼킵니다.
      try {
        console.log(`📋 [일반내용] 추출 시작 (${this.browserId})`);
        this.lastGeneralInfo = await this.extractGeneralInfo(caseNumber);
        if (this.lastGeneralInfo) {
          console.log(`✅ [일반내용] 추출 완료 (${this.browserId})`);
        } else {
          console.log(`⚠️ [일반내용] 추출 결과 없음 (${this.browserId})`);
        }
      } catch (genErr) {
        console.log(`⚠️ [일반내용] 추출 예외(무시하고 진행): ${genErr.message}`);
        this.lastGeneralInfo = null;
      }

      // 1. "진행내용" 탭 클릭 (듀얼 전략)
      console.log(`🔍 [DEBUG] "진행내용" 탭 찾는 중... (ID/텍스트 방식 병행) (${this.browserId})`);
      
      let tabClicked = false;

      // [전략 1] ID 기반 검색 (강화된 병행 방식)
      try {
        const progressTabSelector = '#mf_ssgoTopMainTab_contents_content1_body_wfSsgoDetail_ssgoCsDetailTab_tab_ssgoTab2';
        const progressTab = await this.page.$(progressTabSelector);
        if (progressTab) {
          console.log(`📋 [전략 1] ID로 탭 발견! 클릭 시도... (${this.browserId})`);
          
          // 1단계: Puppeteer click 시도
          try {
            await progressTab.click();
            console.log(`✅ [전략 1-1] Puppeteer click 성공!`);
            tabClicked = true;
          } catch (clickError) {
            console.log(`⚠️ [전략 1-1] Puppeteer click 실패: ${clickError.message}. JS click으로 재시도.`);
          }

          // 2단계: JS click 시도 (1단계 실패 시 또는 보강용)
          if (!tabClicked) {
            await this.page.evaluate((selector) => {
              const el = document.querySelector(selector);
              if (el) el.click();
            }, progressTabSelector);
            tabClicked = true;
            console.log(`✅ [전략 1-2] JS click 성공!`);
          }
        }
      } catch (e) {
        console.log(`⚠️ [전략 1] ID 검색/클릭 프로세스 오류: ${e.message}`);
      }

      // [전략 2] 텍스트 기반 검색 (실패 시 폴백)
      if (!tabClicked) {
        console.log(`🔄 [전략 2] 텍스트 기반 검색 시도...`);
        tabClicked = await this.page.evaluate(() => {
          // li, a, span 태그 중에서 "진행내용" 텍스트를 포함한 요소 찾기
          const elements = document.querySelectorAll('li, a, span');
          for (const el of elements) {
            if (el.textContent.trim() === '진행내용' && el.offsetParent !== null) { // 보이는 요소만
              el.click();
              return true;
            }
          }
          return false;
        });
        
        if (tabClicked) {
          console.log(`✅ [전략 2] 텍스트로 탭 클릭 성공!`);
        }
      }

      if (tabClicked) {
        // 탭 전환 후 그리드가 나타나면 즉시 진행 (아래 waitForSelector에서 대기)
      }
      if (!tabClicked) {
        const errorMsg = `"진행내용" 탭을 찾을 수 없습니다. (ID/텍스트 전략 모두 실패)`;
        console.log(`❌ ${errorMsg} (${this.browserId})`);
        
        // 디버그: 스크린샷
        const debugPath = `screenshots/tab_not_found_${caseNumber || 'unknown'}_${Date.now()}.png`;
        await this.page.screenshot({ path: debugPath, fullPage: true });
        console.log(`📸 [DEBUG] 탭 미발견 스크린샷: ${debugPath}`);
        
        throw new Error(errorMsg);
      }

      // 2. 진행내용 그리드 대기 및 추출
      const gridSelector = '#mf_ssgoTopMainTab_contents_content1_body_wfSsgoDetail_ssgoCsDetailTab_contents_ssgoTab2_body_grd_csProgLst_main_div';
      console.log(`🔍 [DEBUG] 진행내용 그리드(#${gridSelector}) 대기 중... (최대 10초)`);

      try {
        await this.page.waitForSelector(gridSelector, { timeout: 10000 });
        console.log(`✅ 진행내용 그리드 발견! (${this.browserId})`);
      } catch (error) {
        console.log(`⚠️ 기본 그리드 선택자 실패. 대체 선택자 시도... (${this.browserId})`);
        
        // 대체: 탭 컨텐츠 영역 내의 아무 그리드나 찾기
        const tabContentSelector = '#mf_ssgoTopMainTab_contents_content1_body_wfSsgoDetail_ssgoCsDetailTab_contents_ssgoTab2_body';
        const fallbackGrid = await this.page.$(`${tabContentSelector} .w2grid`);
        
        if (fallbackGrid) {
             console.log(`✅ 대체 그리드 발견! (${this.browserId})`);
        } else {
             const errorMsg = `진행내용 그리드를 찾을 수 없습니다: ${error.message}`;
             console.log(`❌ ${errorMsg} (${this.browserId})`);
             
             // 혹시 "조회된 내용이 없습니다" 같은 메시지가 있는지 확인
             const bodyText = await this.page.$eval('body', el => el.innerText);
             if (bodyText.includes('조회된 내용이 없습니다') || bodyText.includes('검색결과가 없습니다')) {
                 console.log(`ℹ️ [DEBUG] 화면에 '내용 없음' 메시지 감지됨 -> 정상 결과(0건)로 처리`);
                 return [];
             }
             
             throw new Error(errorMsg);
        }
      }

      // 데이터 행 로딩 대기: tbody tr이 생기거나 로딩 인디케이터가 사라질 때까지 (최대 5초)
      try {
        await this.page.waitForFunction(
          (selector) => {
            // ID로 찾거나, 없으면 클래스로 찾기 (폴백)
            let grid = document.querySelector(selector);
            if (!grid) {
                // 폴백: 탭 2번 바디 안의 첫 번째 그리드
                grid = document.querySelector('#mf_ssgoTopMainTab_contents_content1_body_wfSsgoDetail_ssgoCsDetailTab_contents_ssgoTab2_body .w2grid');
            }
            if (!grid) return false;
            
            const dataLayer = grid.querySelector('.w2grid_dataLayer');
            const table = dataLayer ? dataLayer.querySelector('table') : grid.querySelector('table');
            if (!table) return false;
            const rows = table.querySelectorAll('tbody tr');
            return rows.length > 0 || !grid.querySelector('.w2grid_loading');
          },
          { timeout: 5000 },
          gridSelector
        );
      } catch (e) {
        // 타임아웃 시 폴백에서 재파싱으로 처리
      }

      const maxParseAttempts = 3;
      let progressData = null;

      for (let attempt = 1; attempt <= maxParseAttempts; attempt++) {
        if (attempt > 1) {
          await new Promise((r) => setTimeout(r, 500));
        }
        console.log(`📋 [DEBUG] 그리드 데이터 파싱 시작... (${this.browserId}) (시도 ${attempt}/${maxParseAttempts})`);

        // 브라우저에서 데이터 추출
        progressData = await this.page.evaluate((selector) => {
        let grid = document.querySelector(selector);
        // 폴백: ID로 못 찾으면 탭 영역 내 첫 그리드로 시도
        if (!grid) {
            grid = document.querySelector('#mf_ssgoTopMainTab_contents_content1_body_wfSsgoDetail_ssgoCsDetailTab_contents_ssgoTab2_body .w2grid');
        }
        if (!grid) return { found: false, rows: 0, data: null };

        // w2grid_dataLayer 내부의 테이블 찾기 (사용자가 제공한 구조)
        const dataLayer = grid.querySelector('.w2grid_dataLayer');
        const targetTable = dataLayer ? dataLayer.querySelector('table') : grid.querySelector('table');
        
        if (!targetTable) return { found: true, rows: 0, data: [] };

        const rows = targetTable.querySelectorAll('tbody tr');
        const data = [];

        rows.forEach((row, index) => {
          const cells = row.querySelectorAll('td');
          if (cells.length >= 4) {
            // 각 셀의 span에서 텍스트와 색상 추출
            const dateSpan = cells[0]?.querySelector('span') || cells[0];
            const contentSpan = cells[1]?.querySelector('span') || cells[1];
            const resultSpan = cells[2]?.querySelector('span') || cells[2];
            const documentSpan = cells[3]?.querySelector('span') || cells[3];

            // 색상 정보 추출 (computedStyle 사용)
            const getColor = (element) => {
              if (!element) return null;
              const style = window.getComputedStyle(element);
              return style.color; // "rgb(255, 0, 0)" 형식
            };

            data.push({
              date: dateSpan?.textContent?.trim() || '',
              content: contentSpan?.textContent?.trim() || '',
              result: resultSpan?.textContent?.trim() || '',
              document: documentSpan?.textContent?.trim() || '',
              // 색상 정보 추가
              dateColor: getColor(dateSpan),
              contentColor: getColor(contentSpan),
              resultColor: getColor(resultSpan),
              documentColor: getColor(documentSpan)
            });
          }
        });

        return { found: true, rows: rows.length, data: data };
      }, gridSelector);

        // 결과 처리: 데이터가 있으면 즉시 반환
        console.log(`📊 [DEBUG] 그리드 발견: ${progressData.found ? 'O' : 'X'}`);
        console.log(`📊 [DEBUG] 파싱된 데이터 수: ${progressData.data ? progressData.data.length : 0}`);

        if (progressData.found && progressData.data && progressData.data.length > 0) {
          console.log(`✅ 진행내용 데이터 추출 완료: ${progressData.data.length}개 행 (${this.browserId})`);
          return progressData.data;
        }
      }

      console.log(`⚠️ 진행내용 데이터가 없습니다 (${this.browserId})`);
      return [];
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

      console.log(`🔍 캡차 요소 찾는 중: ${selector} (${this.browserId})`);

      // 요소가 보일 때까지 대기 (더 긴 시간)
      await this.page.waitForSelector(selector, { timeout: 15000 });

      // 요소가 실제로 보이는지 확인
      const element = await this.page.$(selector);
      if (!element) {
        throw new Error(`요소를 찾을 수 없습니다: ${selector}`);
      }

      // 요소가 화면에 보이는지 확인
      const isVisible = await element.isIntersectingViewport();
      console.log(`👁️ 요소 가시성 확인: ${isVisible} (${this.browserId})`);

      if (!isVisible) {
        // 요소가 보이지 않으면 스크롤해서 보이게 함
        await element.scrollIntoView();
        await this.page.waitForTimeout(1000); // 스크롤 후 대기
      }

      // 요소 크기 확인
      const boundingBox = await element.boundingBox();
      console.log(`📏 요소 크기: ${JSON.stringify(boundingBox)} (${this.browserId})`);

      if (!boundingBox || boundingBox.width === 0 || boundingBox.height === 0) {
        throw new Error(`요소 크기가 0입니다: ${JSON.stringify(boundingBox)}`);
      }

      // 요소만 캡처
      await element.screenshot({
        path: filepath,
        type: 'png'
      });

      // 파일이 실제로 생성되었는지 확인
      const fileExists = await fs.access(filepath).then(() => true).catch(() => false);
      if (!fileExists) {
        throw new Error(`스크린샷 파일이 생성되지 않았습니다: ${filepath}`);
      }

      const stats = await fs.stat(filepath);
      console.log(`📸 요소 스크린샷 저장: ${filename} (${stats.size} bytes) (${this.browserId})`);
      return filepath;
    } catch (error) {
      console.error(`❌ 요소 스크린샷 촬영 실패 (${this.browserId}):`, error.message);

      // 전체 페이지 스크린샷으로 대체 시도
      try {
        console.log(`🔄 전체 페이지 스크린샷으로 대체 시도 (${this.browserId})`);
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
        const filename = `${caseNumber}-${timestamp}-${type}-fullpage.png`;
        const filepath = path.join(this.screenshotsDir, filename);

        await this.page.screenshot({
          path: filepath,
          fullPage: true
        });

        console.log(`📸 전체 페이지 스크린샷 저장: ${filename} (${this.browserId})`);
        return filepath;
      } catch (fallbackError) {
        console.error(`❌ 전체 페이지 스크린샷도 실패 (${this.browserId}):`, fallbackError.message);
        throw error;
      }
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

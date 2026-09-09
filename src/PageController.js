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
   * 주니어 참고:
   * - 1차 시도는 networkidle2 (완전한 로딩)
   * - 재시도는 domcontentloaded 로 완화 (동시 접속 시 idle 대기가 자주 타임아웃남)
   * - CASEING_* 환경변수는 Python(puppeteer.py)이 넘깁니다. 없으면 구버전과 동일하게 동작.
   */
  async navigateToSite() {
    const gotoTimeout = parseInt(process.env.CASEING_GOTO_TIMEOUT_MS, 10) || 30000;
    const maxRetry = parseInt(process.env.CASEING_NAV_MAX_RETRY, 10) || 0;
    const retryDelayMs = parseInt(process.env.CASEING_NAV_RETRY_DELAY_MS, 10) || 3000;
    const totalAttempts = 1 + Math.max(0, maxRetry);
    let lastError = null;

    // 폰트/미디어/스타일시트·광고 차단 (캡차 image 는 유지)
    try {
      await this._enableLightRequestBlocking();
    } catch (e) {
      console.log(`⚠️ 리소스 차단 설정 실패(무시): ${e.message}`);
    }

    for (let attempt = 1; attempt <= totalAttempts; attempt++) {
      try {
        // 주니어: networkidle2 는 광고/분석 요청 때문에 자주 타임아웃남.
        // select 대기만으로 충분하므로 domcontentloaded 사용.
        const waitUntil = 'domcontentloaded';
        if (attempt === 1) {
          console.log(`🌐 대법원 사이트 접속 중... (${this.browserId})`);
        } else {
          console.log(
            `🔁 사이트 접속 재시도 (${attempt - 1}/${maxRetry}) waitUntil=${waitUntil} (${this.browserId})`
          );
          await new Promise((r) => setTimeout(r, retryDelayMs));
        }

        await this.page.goto('https://ssgo.scourt.go.kr/ssgo/index.on?cortId=www', {
          waitUntil,
          timeout: gotoTimeout
        });

        // 페이지 로딩 완료 대기
        await this.page.waitForSelector('body', { timeout: 10000 });

        console.log(`✅ 사이트 접속 완료 (${this.browserId})`);
        // body 직후엔 WebSquare 검색 폼·최근검색이 아직 없을 수 있습니다.
        // 스마트 스킵은 waitForSearchForm + scanRecentCase 에서 한 번 더 기다립니다.
        return true;
      } catch (error) {
        lastError = error;
        console.error(
          `⚠️ 사이트 접속 시도 ${attempt}/${totalAttempts} 실패 (${this.browserId}):`,
          error.message
        );
        // Python stderr 파일/필터와 무관하게 보이게 stdout에도 남김
        console.log(
          `⚠️ 사이트 접속 시도 ${attempt}/${totalAttempts} 실패 (${this.browserId}): ${error.message}`
        );
      }
    }

    console.error(`❌ 사이트 접속 실패 (${this.browserId}):`, lastError && lastError.message);
    console.log(
      `❌ 사이트 접속 실패 (${this.browserId}): ${(lastError && lastError.message) || ''}`
    );
    throw lastError;
  }

  /**
   * 불필요 리소스 차단으로 메모리·속도를 줄입니다.
   * 캡차는 <img> 이므로 image 타입은 절대 막지 않습니다.
   *
   * 주니어 참고:
   * - 플래그는 컨트롤러가 아니라 page 에 둡니다.
   *   워커가 같은 page 를 재사용할 때 리스너가 중복 등록되면
   *   한 요청에 continue 가 두 번 불려 "Request is already handled!" 로
   *   Node 프로세스가 죽습니다.
   * - req.continue()/abort() 는 Promise 를 반환합니다.
   *   try/catch 는 동기 예외만 잡으므로 .catch(() => {}) 로
   *   unhandled rejection 을 반드시 막아야 합니다 (Node 22는 그걸로 종료).
   */
  async _enableLightRequestBlocking() {
    // page 단위 중복 등록 방지 (컨트롤러 인스턴스가 바뀌어도 한 번만)
    if (this.page.__caseIngBlockingEnabled) return;
    this.page.__caseIngBlockingEnabled = true;
    this._requestBlockingEnabled = true;

    await this.page.setRequestInterception(true);
    const blockedTypes = new Set(['font', 'media', 'stylesheet']);
    const blockedHostHints = [
      'google-analytics',
      'googletagmanager',
      'doubleclick',
      'facebook',
      'hotjar',
      'clarity.ms'
    ];

    // Promise rejection 이 프로세스를 죽이지 않도록 삼킴
    const safeAbort = (req) => {
      try {
        const p = req.abort();
        if (p && typeof p.catch === 'function') p.catch(() => {});
      } catch (_) { /* ignore */ }
    };
    const safeContinue = (req) => {
      try {
        const p = req.continue();
        if (p && typeof p.catch === 'function') p.catch(() => {});
      } catch (_) { /* ignore */ }
    };

    this.page.on('request', (req) => {
      try {
        // 다른 리스너가 이미 처리했으면 절대 다시 continue/abort 하지 않음
        if (typeof req.isInterceptResolutionHandled === 'function'
            && req.isInterceptResolutionHandled()) {
          return;
        }
        const type = req.resourceType();
        const url = req.url().toLowerCase();
        if (blockedTypes.has(type)) {
          safeAbort(req);
          return;
        }
        if (blockedHostHints.some((h) => url.includes(h))) {
          safeAbort(req);
          return;
        }
        safeContinue(req);
      } catch (e) {
        safeContinue(req);
      }
    });
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
   * 주니어 참고:
   * - select 태그만 있고 option 이 비어 있으면(WebSquare 로딩 중) 인덱스 -1 로 바로 죽습니다.
   * - 그래서 option 이 채워질 때까지 기다린 뒤 매칭하고, 그래도 없으면 reload 후 1회 재시도합니다.
   * - 대기 시간은 CASEING_GOTO_TIMEOUT_MS 의 절반(최소 15초)을 씁니다.
   */
  async selectCourt(courtName) {
    try {
      console.log(`🏛️ 법원 선택 중: ${courtName} (${this.browserId})`);

      const gotoTimeout = parseInt(process.env.CASEING_GOTO_TIMEOUT_MS, 10) || 30000;
      // select·옵션 대기는 goto 타임아웃의 절반, 최소 15초
      const selectTimeout = Math.max(15000, Math.floor(gotoTimeout / 2));

      const waitForCourtSelectReady = async () => {
        await this.page.waitForSelector('select', { timeout: selectTimeout });
        // option 이 충분히 생기거나, 목표 법원 텍스트가 보일 때까지 대기
        await this.page.waitForFunction(
          (expected) => {
            const sel = document.querySelector('select');
            if (!sel || !sel.options || sel.options.length < 5) return false;
            if (!expected) return sel.options.length >= 20;
            for (let i = 0; i < sel.options.length; i++) {
              const t = (sel.options[i].text || '').trim();
              if (t === expected || t.includes(expected)) return true;
            }
            // 아직 목표 법원은 없지만 옵션이 많이 채워졌으면 매칭 단계로 진행
            return sel.options.length >= 50;
          },
          { timeout: selectTimeout },
          courtName
        );
      };

      try {
        await waitForCourtSelectReady();
      } catch (waitErr) {
        console.log(
          `⚠️ select/옵션 미준비 → 페이지 새로고침 후 재시도 (${this.browserId}): ${waitErr.message}`
        );
        try {
          await this.page.reload({ waitUntil: 'domcontentloaded', timeout: gotoTimeout });
        } catch (reloadErr) {
          console.error(`⚠️ 페이지 reload 실패 (${this.browserId}):`, reloadErr.message);
        }
        await waitForCourtSelectReady();
      }

      const tryMatchAndSelect = async () => {
        const selects = await this.page.$$('select');
        console.log(`🔍 발견된 select 요소 수: ${selects.length} (${this.browserId})`);

        const select = selects[0];
        if (!select) {
          throw new Error('select 요소를 찾을 수 없습니다');
        }

        const options = await select.$$eval('option', (opts) =>
          opts.map((option) => option.text)
        );
        console.log(`📋 법원 옵션들:`, options.slice(0, 10), `... (총 ${options.length})`);

        let courtIndex = options.findIndex((opt) => opt === courtName);
        if (courtIndex === -1) {
          courtIndex = options.findIndex((opt) => opt.includes(courtName));
        }
        console.log(`🔍 ${courtName} 검색 결과: 인덱스 ${courtIndex} (${this.browserId})`);
        return { select, options, courtIndex };
      };

      let { select, options, courtIndex } = await tryMatchAndSelect();

      // 옵션은 있는데 매칭 실패 → 한 번 더 reload 후 재검색 (레이스 완화)
      if (courtIndex < 0) {
        console.log(
          `⚠️ 법원 미매칭(옵션 ${options.length}개) → reload 후 재검색 (${this.browserId})`
        );
        try {
          await this.page.reload({ waitUntil: 'domcontentloaded', timeout: gotoTimeout });
        } catch (reloadErr) {
          console.error(`⚠️ 페이지 reload 실패 (${this.browserId}):`, reloadErr.message);
        }
        try {
          await waitForCourtSelectReady();
        } catch (_) {
          // 아래에서 최종 에러
        }
        ({ select, options, courtIndex } = await tryMatchAndSelect());
      }

      if (courtIndex >= 0) {
        console.log(`✅ ${courtName} 발견! 선택 중... (${this.browserId})`);

        const currentValue = await select.evaluate((el) => el.value);
        const currentText = await select.evaluate(
          (el) => el.options[el.selectedIndex]?.text || ''
        );
        console.log(`현재 선택된 값: ${currentValue}, 텍스트: ${currentText} (${this.browserId})`);

        await Promise.race([
          select.evaluate((element, index) => {
            element.selectedIndex = index;
            element.dispatchEvent(new Event('change', { bubbles: true }));
            element.dispatchEvent(new Event('input', { bubbles: true }));
          }, courtIndex),
          new Promise((_, reject) =>
            setTimeout(() => reject(new Error('법원 선택 evaluate 타임아웃(15초)')), 15000)
          ),
        ]);

        try {
          await this.page.waitForFunction(
            (expectedText) => {
              const sel = document.querySelector('select');
              return (
                sel &&
                sel.options[sel.selectedIndex] &&
                sel.options[sel.selectedIndex].text === expectedText
              );
            },
            { timeout: 5000 },
            courtName
          );
        } catch (e) {
          // 타임아웃 시 아래 검증으로 진행
        }

        const newValue = await select.evaluate((el) => el.value);
        const newText = await select.evaluate(
          (el) => el.options[el.selectedIndex]?.text || ''
        );
        console.log(`선택 후 값: ${newValue}, 텍스트: ${newText} (${this.browserId})`);

        // 정확 일치 또는 부분 일치(매칭에 includes 를 쓴 경우) 모두 허용
        if (newText === courtName || (newText && newText.includes(courtName))) {
          console.log(`✅ ${courtName} 선택 성공! (${this.browserId})`);
          return true;
        }
        console.log(`❌ 선택 실패: 예상=${courtName}, 실제=${newText} (${this.browserId})`);
        throw new Error(`법원 선택 실패: ${courtName}`);
      }

      console.log(`❌ ${courtName}를 찾을 수 없습니다. (${this.browserId})`);
      console.log(
        `사용 가능한 법원들:`,
        options.filter((opt) => !opt.includes('---')).slice(0, 30)
      );
      throw new Error(`${courtName}를 찾을 수 없습니다`);
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
   * 검색 화면(사건번호 입력칸)이 뜰 때까지 기다립니다.
   *
   * 주니어: navigateToSite() 는 body 만 봅니다.
   * 대법원 WebSquare 는 최근 검색 목록을 그 다음 AJAX 로 붙입니다.
   * 접속 직후 스캔하면 항상 "최근 검색 내역 없음" 이 됩니다.
   */
  async waitForSearchForm(timeoutMs = 10000) {
    const selector = '#mf_ssgoTopMainTab_contents_content1_body_ibx_fullCsNo';
    try {
      await this.page.waitForSelector(selector, { timeout: timeoutMs });
      console.log(`✅ [Smart Skip] 검색 폼 준비됨 (${this.browserId})`);
      return true;
    } catch (_) {
      console.log(`⚠️ [Smart Skip] 검색 폼 대기 타임아웃 (${this.browserId})`);
      return false;
    }
  }

  /**
   * 최근 검색 목록에서 사건번호가 보이는지 확인합니다.
   *
   * 주니어:
   * - 공백/하이픈을 빼고 비교합니다. (2026가합7478 vs 2026 가합 7478)
   * - a/td 정확 일치만 보면 span 안 번호나 칸 안 여분 글자에 실패합니다.
   * - 짧은 칸만 보고, 페이지 전체 텍스트는 제외합니다.
   * - waitMs 동안 0.4초 간격으로 다시 봅니다 (목록이 늦게 그려짐).
   */
  async scanRecentCase(caseNumber, waitMs = 8000) {
    const target = String(caseNumber || '').replace(/[\s\-]/g, '');
    const started = Date.now();
    let lastSample = '';

    while (Date.now() - started < waitMs) {
      const result = await this.page.evaluate((targetNorm) => {
        const norm = (s) => String(s || '').replace(/[\s\-]/g, '');
        const samples = [];
        let foundHint = '';
        const nodes = document.querySelectorAll('a, td, span, li');
        for (const el of nodes) {
          const raw = (el.innerText || el.textContent || '').trim();
          if (!raw || raw.length > 60) continue;
          const n = norm(raw);
          // 사건번호처럼 보이는 짧은 칸만 샘플로 남김 (진단 로그용)
          if (n && n.length >= 6 && n.length <= 30 && /[0-9]/.test(n) && /[가-힣]/.test(n)) {
            if (samples.length < 8 && samples.indexOf(raw) === -1) {
              samples.push(raw);
            }
          }
          if (!targetNorm) continue;
          if (n === targetNorm || (targetNorm.length >= 8 && n.includes(targetNorm))) {
            foundHint = raw;
            break;
          }
        }
        return { foundHint, samples };
      }, target);

      lastSample = (result.samples || []).join(', ');
      if (result.foundHint) {
        return { found: true, hint: result.foundHint, sample: lastSample };
      }
      await new Promise((r) => setTimeout(r, 400));
    }
    return { found: false, hint: '', sample: lastSample };
  }

  /**
   * 최근 검색 결과 클릭 (캡차 스킵용)
   */
  async clickRecentCase(caseNumber) {
    try {
      console.log(`🖱️ [SMART SKIP] 최근 검색 결과 클릭 시도: ${caseNumber} (${this.browserId})`);

      // scan 과 같은 정규화·느슨 매칭. a 가 아니면 가장 가까운 링크를 클릭합니다.
      const clicked = await this.page.evaluate((targetNo) => {
        const norm = (s) => String(s || '').replace(/[\s\-]/g, '');
        const target = norm(targetNo);
        const nodes = document.querySelectorAll('a, td, span, li');
        for (const el of nodes) {
          const raw = (el.innerText || el.textContent || '').trim();
          if (!raw || raw.length > 60) continue;
          const n = norm(raw);
          if (n === target || (target.length >= 8 && n.includes(target))) {
            const clickable = (typeof el.closest === 'function' && el.closest('a')) || el;
            clickable.click();
            return true;
          }
        }
        return false;
      }, caseNumber);

      if (clicked) {
        console.log(`✅ [SMART SKIP] 최근 검색 결과 클릭 성공 (${this.browserId})`);

        // 주니어 참고 (2026-08-12 사고):
        // WebSquare는 이전 화면의 탭 DOM을 남겨 둡니다.
        // "탭 엘리먼트가 존재하는가"만 보면 화면이 안 바뀌었는데도 즉시 통과해
        // 진행내용 그리드를 못 찾고, 빈 배열([])이 정상 0건으로 둔갑했습니다.
        // 상세 영역(wfSsgoDetail) 안에 해당 사건번호 + 기본내용 표지가
        // 실제로 렌더될 때까지 기다립니다.
        try {
          await this.page.waitForFunction((targetNo) => {
            const detail = document.querySelector('[id*="wfSsgoDetail"]');
            if (!detail) return false;
            const text = (detail.innerText || '').replace(/\s+/g, '');
            const target = String(targetNo || '').replace(/\s+/g, '');
            if (!target || !text.includes(target)) return false;
            return text.includes('기본내용') || text.includes('사건명') || text.includes('원고');
          }, { timeout: 8000 }, caseNumber);
          console.log(`✅ [SMART SKIP] 상세 화면 렌더 확인 (${this.browserId})`);
          // 탭/그리드가 안정화될 시간을 조금 더 줍니다.
          await new Promise(resolve => setTimeout(resolve, 1000));
        } catch (e) {
          console.log(`⚠️ [SMART SKIP] 상세 화면 렌더 대기 타임아웃 — 2초 보조 대기 (${this.browserId})`);
          await new Promise(resolve => setTimeout(resolve, 2000));
        }
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

      // 1. "진행내용" 탭 클릭
      // 주니어: click()이 예외 없이 끝나도 탭이 실제로 전환되지 않을 수 있음.
      // → 클릭 후 탭 바디가 보이는지 확인하고, 실패하면 JS click → 텍스트 전략 순으로 시도.
      console.log(`🔍 [DEBUG] "진행내용" 탭 찾는 중... (ID/텍스트 방식 병행) (${this.browserId})`);

      // progressTabSelector 는 위에서 이미 선언됨
      const tabBodySelector = '#mf_ssgoTopMainTab_contents_content1_body_wfSsgoDetail_ssgoCsDetailTab_contents_ssgoTab2_body';

      // 탭 바디가 화면에 보이는지 확인 (클릭 성공 판정용)
      const isTabBodyVisible = async (timeoutMs = 2000) => {
        try {
          await this.page.waitForFunction((sel) => {
            const tabBody = document.querySelector(sel);
            if (!tabBody) return false;
            const style = window.getComputedStyle(tabBody);
            return style.display !== 'none' && style.visibility !== 'hidden';
          }, { timeout: timeoutMs }, tabBodySelector);
          return true;
        } catch (e) {
          return false;
        }
      };

      let tabActivated = false;

      // [전략 1-1] Puppeteer click
      try {
        const progressTab = await this.page.$(progressTabSelector);
        if (progressTab) {
          console.log(`📋 [전략 1] ID로 탭 발견! Puppeteer click 시도... (${this.browserId})`);
          try {
            await progressTab.click();
            console.log(`✅ [전략 1-1] Puppeteer click 호출 완료 — 전환 확인 중...`);
            tabActivated = await isTabBodyVisible(2000);
            if (tabActivated) {
              console.log(`✅ [전략 1-1] 탭 전환 확인됨`);
            } else {
              console.log(`⚠️ [전략 1-1] 클릭은 됐지만 탭 바디가 안 보임 → JS click 폴백`);
            }
          } catch (clickError) {
            console.log(`⚠️ [전략 1-1] Puppeteer click 실패: ${clickError.message}`);
          }

          // [전략 1-2] JS click (1-1 미확인 시 항상 시도)
          if (!tabActivated) {
            await this.page.evaluate((selector) => {
              const el = document.querySelector(selector);
              if (el) el.click();
            }, progressTabSelector);
            console.log(`✅ [전략 1-2] JS click 호출 완료 — 전환 확인 중...`);
            tabActivated = await isTabBodyVisible(2000);
            if (tabActivated) {
              console.log(`✅ [전략 1-2] 탭 전환 확인됨`);
            } else {
              console.log(`⚠️ [전략 1-2] JS click 후에도 탭 바디 미표시`);
            }
          }
        }
      } catch (e) {
        console.log(`⚠️ [전략 1] ID 검색/클릭 프로세스 오류: ${e.message}`);
      }

      // [전략 2] 텍스트 기반 검색 (실패 시 폴백)
      if (!tabActivated) {
        console.log(`🔄 [전략 2] 텍스트 기반 검색 시도...`);
        const textClicked = await this.page.evaluate(() => {
          const elements = document.querySelectorAll('li, a, span');
          for (const el of elements) {
            if (el.textContent.trim() === '진행내용' && el.offsetParent !== null) {
              el.click();
              return true;
            }
          }
          return false;
        });
        if (textClicked) {
          tabActivated = await isTabBodyVisible(2000);
          if (tabActivated) {
            console.log(`✅ [전략 2] 텍스트로 탭 전환 확인됨`);
          } else {
            console.log(`⚠️ [전략 2] 텍스트 클릭 후에도 탭 바디 미표시`);
          }
        }
      }

      if (!tabActivated) {
        const errorMsg = `"진행내용" 탭을 찾을 수 없습니다. (ID/텍스트 전략 모두 실패)`;
        console.log(`❌ ${errorMsg} (${this.browserId})`);

        // 디버그 스크린샷 — 절대 경로 + 디렉터리 보장
        try {
          await fs.mkdir(this.screenshotsDir, { recursive: true });
          const debugPath = path.join(
            this.screenshotsDir,
            `tab_not_found_${caseNumber || 'unknown'}_${Date.now()}.png`
          );
          await this.page.screenshot({ path: debugPath, fullPage: true });
          console.log(`📸 [DEBUG] 탭 미발견 스크린샷: ${debugPath}`);
        } catch (ssErr) {
          console.log(`⚠️ [DEBUG] 탭 미발견 스크린샷 저장 실패: ${ssErr.message}`);
        }

        throw new Error(errorMsg);
      }

      // 2. 진행내용 그리드 대기 및 추출
      const gridSelector = '#mf_ssgoTopMainTab_contents_content1_body_wfSsgoDetail_ssgoCsDetailTab_contents_ssgoTab2_body_grd_csProgLst_main_div';
      console.log(`🔍 [DEBUG] 진행내용 그리드(#${gridSelector}) 대기 중... (최대 8초)`);

      try {
        await this.page.waitForSelector(gridSelector, { timeout: 8000 });
        console.log(`✅ 진행내용 그리드 발견! (${this.browserId})`);
      } catch (error) {
        console.log(`⚠️ 기본 그리드 선택자 실패. 대체 선택자 시도... (${this.browserId})`);
        
        // 대체: 탭 컨텐츠 영역 내의 아무 그리드나 찾기
        const tabContentSelector = '#mf_ssgoTopMainTab_contents_content1_body_wfSsgoDetail_ssgoCsDetailTab_contents_ssgoTab2_body';
        const fallbackGrid =
          (await this.page.$(`${tabContentSelector} .w2grid`)) ||
          (await this.page.$(`${tabContentSelector} [id*="grd_csProgLst"]`)) ||
          (await this.page.$(`${tabContentSelector} div.w2grid_main_div`));
        
        if (fallbackGrid) {
             console.log(`✅ 대체 그리드 발견! (${this.browserId})`);
        } else {
             const errorMsg = `진행내용 그리드를 찾을 수 없습니다: ${error.message}`;
             console.log(`❌ ${errorMsg} (${this.browserId})`);

             // 스크린샷을 먼저 남긴 뒤 body 텍스트 판정 (판정 예외로 스크린샷이 날아가지 않게)
             try {
               await fs.mkdir(this.screenshotsDir, { recursive: true });
               const debugPath = path.join(
                 this.screenshotsDir,
                 `grid_not_found_${caseNumber || 'unknown'}_${Date.now()}.png`
               );
               await this.page.screenshot({ path: debugPath, fullPage: true });
               console.log(`📸 [DEBUG] 그리드 미발견 스크린샷: ${debugPath}`);
             } catch (ssErr) {
               console.log(`⚠️ [DEBUG] 그리드 미발견 스크린샷 저장 실패: ${ssErr.message}`);
             }

             // 탭 컨텐츠 DOM 일부 로그 (사후 분석용)
             try {
               const htmlSnippet = await this.page.evaluate((sel) => {
                 const el = document.querySelector(sel);
                 return el ? (el.outerHTML || '').slice(0, 500) : '(탭 컨텐츠 없음)';
               }, tabContentSelector);
               console.log(`📋 [DEBUG] 탭 컨텐츠 HTML 앞부분: ${htmlSnippet}`);
             } catch (domErr) {
               console.log(`⚠️ [DEBUG] 탭 컨텐츠 HTML 읽기 실패: ${domErr.message}`);
             }

             let bodyText = '';
             try {
               bodyText = await this.page.$eval('body', el => el.innerText);
             } catch (bodyErr) {
               console.log(`⚠️ [DEBUG] body 텍스트 읽기 실패: ${bodyErr.message}`);
             }
             if (bodyText.includes('자동입력방지') || bodyText.includes('일치하지')) {
                 throw new Error(`WRONG_CAPTCHA: ${error.message}`);
             }
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
      // 주니어 참고 (2026-08-12 사고):
      // 여기서 return [] 하면 호출부는 "조회 성공, 진행내용 0건"으로 오인합니다.
      // 실패는 실패로 다시 던져서 Python이 시트를 덮어쓰지 못하게 합니다.
      // 진짜 0건은 위쪽 "조회된 내용이 없습니다" 분기에서만 return [] 합니다.
      console.error(`❌ 진행내용 데이터 추출 실패 (${this.browserId}):`, error.message);
      throw error;
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

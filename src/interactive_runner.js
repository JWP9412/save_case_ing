#!/usr/bin/env node
/**
 * 대화형 Puppeteer 실행 스크립트 (Interactive Runner)
 * =================================================
 *
 * 모드 1 (레거시, 1건 후 종료):
 *   node src/interactive_runner.js <사건번호> <피고> <법원> [인스턴스번호]
 *
 * 모드 2 (레인 워커, Chrome 재사용):
 *   node src/interactive_runner.js --worker <기본인스턴스번호>
 *   stdin JSON:
 *     {"cmd":"CASE","caseNumber":"...","defendant":"...","court":"...","instanceIndex":0,"smartSkip":true}
 *     {"cmd":"QUIT"}
 *   사건 처리 후 프로세스를 유지하고 다음 CASE를 기다립니다.
 */

const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs').promises;
const readline = require('readline');
const PageController = require('./PageController');
const maintenance = require('../maintenance.js');

const args = process.argv.slice(2);
const isWorkerMode = args[0] === '--worker';

const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
    terminal: false
});

rl.on('close', () => {
    process.exit(0);
});

function waitForInput() {
    return new Promise((resolve) => {
        rl.once('line', (line) => {
            resolve((line || '').trim());
        });
    });
}

/** Chrome 저메모리 launch args */
function chromeArgs() {
    return [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--window-size=1024,768',
        '--disable-blink-features=AutomationControlled',
        '--disable-infobars',
        '--remote-debugging-port=0',
        '--disable-dev-shm-usage',
        '--disable-gpu',
        '--disable-extensions',
        '--disable-default-apps',
        '--disable-sync',
        '--disable-background-networking',
        '--disable-component-update',
        '--disable-client-side-phishing-detection',
        '--renderer-process-limit=1',
        '--js-flags=--max-old-space-size=256'
    ];
}

async function launchBrowser(instanceIndex) {
    const userDataDir = path.join(process.cwd(), 'cookie_data_for_save', `instance_${instanceIndex}`);
    await fs.mkdir(userDataDir, { recursive: true }).catch(() => { });
    console.log(`🚀 [Interactive] Chrome 기동 instance_${instanceIndex}`);
    const browser = await puppeteer.launch({
        headless: maintenance.browserHeadless,
        userDataDir: userDataDir,
        args: chromeArgs()
    });
    const pages = await browser.pages();
    const page = pages[0] || await browser.newPage();
    return { browser, page, instanceIndex };
}

/**
 * 한 사건을 처리합니다. 캡차/CLICK 입력까지 포함한 뒤 JSON_RESULT 를 출력합니다.
 * 워커 모드에서는 종료하지 않습니다.
 */
async function processOneCase(page, caseNumber, defendant, court, smartSkipEnabled) {
    let wrongCaptchaOccurred = false;

    // 이전 리스너 중복 방지를 위해 새 dialog 핸들러는 page 단위로 한 번만 붙이도록
    // (워커에서는 재진입 시 기존 핸들러가 남아 있을 수 있음 → 플래그만 공유)
    const onDialog = async (dialog) => {
        const msg = dialog.message();
        console.log(`💬 [Interactive] 알림창 감지: ${msg} (${dialog.type()})`);
        try {
            if (msg.includes('자동입력방지') || msg.includes('일치하지')) {
                wrongCaptchaOccurred = true;
                console.log('⚠️ [Interactive] 캡차 불일치 - 재입력 대기 모드');
            }
            await dialog.accept();
            console.log('✅ [Interactive] 알림창 닫음 (수락)');
        } catch (error) {
            console.error('❌ [Interactive] 알림창 처리 실패:', error.message);
        }
    };
    page.removeAllListeners('dialog');
    page.on('dialog', onDialog);

    const controller = new PageController(page, 'interactive');
    await controller.navigateToSite();

    let foundInRecent = false;
    if (smartSkipEnabled) {
        console.log(`🔍 [Smart Skip] 최근 검색 내역 확인 중: ${caseNumber}`);
        foundInRecent = await page.evaluate((targetNo) => {
            const elements = document.querySelectorAll('a, td');
            for (const el of elements) {
                if (el.textContent.trim() === targetNo) {
                    return true;
                }
            }
            return false;
        }, caseNumber);
    } else {
        console.log(`ℹ️ [Smart Skip] 설정으로 비활성화됨 (${caseNumber})`);
    }

    if (foundInRecent) {
        console.log(`✅ [Smart Skip] 최근 검색 내역 발견!`);
        console.log('CAPTCHA_STATUS: SKIP_AND_CLICK');
    } else {
        console.log(`ℹ️ [Smart Skip] 최근 검색 내역 없음 -> 정보 입력 진행`);
        await controller.selectCourt(court);
        await controller.checkCaseNumberInputMode();
        await controller.checkSaveSearchResult();
        await controller.inputCaseNumber(caseNumber);
        await controller.inputPartyName(defendant);

        const captchaSelector = '#mf_ssgoTopMainTab_contents_content1_body_img_captcha';
        await page.waitForSelector(captchaSelector, { timeout: 15000 });

        const screenshotsDir = path.join(process.cwd(), 'screenshots');
        await fs.mkdir(screenshotsDir, { recursive: true }).catch(() => { });
        const filename = `${caseNumber}-${Date.now()}-captcha.png`;
        const filepath = path.join(screenshotsDir, filename);
        const element = await page.$(captchaSelector);
        await element.screenshot({ path: filepath });
        console.log(`🖼️ GUI_IMAGE_PATH: ${filepath}`);
    }

    let progressData = null;
    while (true) {
        console.log('⏳ [Interactive] 입력 대기 중...');
        const input = await waitForInput();
        console.log(`📥 [Interactive] 입력 수신: ${input}`);

        // 워커 모드에서 다음 사건이 오면 현재 건을 중단할 수 없음 — 캡차/CLICK만 허용
        if (input.startsWith('{') && input.includes('"cmd"')) {
            console.log('⚠️ [Interactive] 캡차 대기 중 CASE/QUIT 수신 — 무시하고 계속 대기');
            continue;
        }

        if (input === 'CLICK') {
            await controller.clickRecentCase(caseNumber);
            progressData = await controller.extractProgressData(caseNumber);
            break;
        }
        if (input === 'FORCE_CAPTCHA') {
            foundInRecent = false;
            console.log('ℹ️ [Interactive] FORCE_CAPTCHA 수신 - 캡차 경로로 전환');
            await controller.selectCourt(court);
            await controller.checkCaseNumberInputMode();
            await controller.checkSaveSearchResult();
            await controller.inputCaseNumber(caseNumber);
            await controller.inputPartyName(defendant);
            const captchaSelector = '#mf_ssgoTopMainTab_contents_content1_body_img_captcha';
            await page.waitForSelector(captchaSelector, { timeout: 15000 });
            const screenshotsDir = path.join(process.cwd(), 'screenshots');
            await fs.mkdir(screenshotsDir, { recursive: true }).catch(() => { });
            const filename = `${caseNumber}-${Date.now()}-captcha-force.png`;
            const filepath = path.join(screenshotsDir, filename);
            const element = await page.$(captchaSelector);
            await element.screenshot({ path: filepath });
            console.log(`WRONG_CAPTCHA_IMAGE: ${filepath}`);
            continue;
        }

        wrongCaptchaOccurred = false;
        await controller.inputCaptcha(input);
        await controller.performSearch(input);

        if (wrongCaptchaOccurred) {
            const captchaSelector = '#mf_ssgoTopMainTab_contents_content1_body_img_captcha';
            try {
                await page.waitForSelector(captchaSelector, { timeout: 5000 });
                await page.click(captchaSelector);
                await new Promise(r => setTimeout(r, 1500));
            } catch (e) {
                console.error('⚠️ [Interactive] 캡차 새로고침 클릭 실패:', e.message);
            }
            const screenshotsDir = path.join(process.cwd(), 'screenshots');
            await fs.mkdir(screenshotsDir, { recursive: true }).catch(() => {});
            const filename = `${caseNumber}-${Date.now()}-captcha-retry.png`;
            const filepath = path.join(screenshotsDir, filename);
            try {
                const el = await page.$(captchaSelector);
                if (el) await el.screenshot({ path: filepath });
            } catch (e) {
                console.error('⚠️ [Interactive] 재시도 캡차 스크린샷 실패:', e.message);
            }
            console.log(`WRONG_CAPTCHA_IMAGE: ${filepath}`);
            continue;
        }

        progressData = await controller.extractProgressData(caseNumber);
        break;
    }

    const result = {
        caseNumber,
        defendant,
        court,
        progressData,
        generalInfo: (controller && controller.lastGeneralInfo) || null,
        success: true,
        timestamp: new Date().toISOString()
    };
    console.log('JSON_RESULT_START');
    console.log(JSON.stringify(result));
    console.log('JSON_RESULT_END');
}

async function runLegacy() {
    if (args.length < 3) {
        console.error('사용법: node src/interactive_runner.js <사건번호> <피고> <법원> [인스턴스번호]');
        console.error('   또는: node src/interactive_runner.js --worker <인스턴스번호>');
        process.exit(1);
    }
    const [caseNumber, defendant, court] = args;
    const instanceIndex = args.length >= 4 ? parseInt(args[3], 10) || 0 : 0;
    let browser = null;
    try {
        console.log(`🚀 [Interactive] 사건 처리 시작: ${caseNumber}`);
        const launched = await launchBrowser(instanceIndex);
        browser = launched.browser;
        const page = launched.page;
        const smartSkipEnabled = String(process.env.CASEING_SMART_SKIP_ENABLED || '1') !== '0';
        await processOneCase(page, caseNumber, defendant, court, smartSkipEnabled);
    } catch (error) {
        console.error(`❌ [Interactive] 오류 발생: ${error.message}`);
        console.log('JSON_RESULT_START');
        console.log(JSON.stringify({ success: false, error: error.message }));
        console.log('JSON_RESULT_END');
    } finally {
        if (browser) {
            await browser.close();
        }
        rl.close();
        process.exit(0);
    }
}

async function runWorker() {
    let currentInstance = parseInt(args[1], 10) || 0;
    let browser = null;
    let page = null;

    console.log(`WORKER_READY instance=${currentInstance}`);

    try {
        while (true) {
            console.log('⏳ [Worker] CASE/QUIT 대기 중...');
            const line = await waitForInput();
            if (!line) continue;

            let msg;
            try {
                msg = JSON.parse(line);
            } catch (e) {
                console.log(`⚠️ [Worker] JSON 아님(무시): ${line.slice(0, 80)}`);
                continue;
            }

            if (msg.cmd === 'QUIT') {
                console.log('👋 [Worker] QUIT 수신 — 종료');
                break;
            }
            if (msg.cmd !== 'CASE') {
                console.log(`⚠️ [Worker] 알 수 없는 cmd: ${msg.cmd}`);
                continue;
            }

            const caseNumber = msg.caseNumber || '';
            const defendant = msg.defendant || '';
            const court = msg.court || '';
            const instanceIndex = parseInt(msg.instanceIndex, 10);
            const profile = Number.isFinite(instanceIndex) ? instanceIndex : currentInstance;
            const smartSkipEnabled = msg.smartSkip !== false
                && String(process.env.CASEING_SMART_SKIP_ENABLED || '1') !== '0';

            console.log(`🚀 [Interactive] 사건 처리 시작: ${caseNumber} [instance_${profile}]`);

            try {
                // 프로필이 바뀌면 Chrome 재기동
                if (!browser || profile !== currentInstance) {
                    if (browser) {
                        try { await browser.close(); } catch (_) { /* ignore */ }
                        browser = null;
                        page = null;
                    }
                    const launched = await launchBrowser(profile);
                    browser = launched.browser;
                    page = launched.page;
                    currentInstance = profile;
                } else {
                    // 같은 프로필: 페이지를 초기화하고 사이트로 다시 이동
                    try {
                        await page.goto('about:blank', { waitUntil: 'domcontentloaded', timeout: 10000 });
                    } catch (_) { /* ignore */ }
                }

                await processOneCase(page, caseNumber, defendant, court, smartSkipEnabled);
                console.log('WORKER_IDLE');
            } catch (error) {
                console.error(`❌ [Interactive] 오류 발생: ${error.message}`);
                console.log('JSON_RESULT_START');
                console.log(JSON.stringify({ success: false, error: error.message }));
                console.log('JSON_RESULT_END');
                console.log('WORKER_IDLE');
                // 오류 후 브라우저가 불안정할 수 있어 다음 건에서 재기동하도록 닫음
                if (browser) {
                    try { await browser.close(); } catch (_) { /* ignore */ }
                    browser = null;
                    page = null;
                }
            }
        }
    } finally {
        if (browser) {
            try { await browser.close(); } catch (_) { /* ignore */ }
        }
        rl.close();
        process.exit(0);
    }
}

if (isWorkerMode) {
    runWorker();
} else {
    runLegacy();
}

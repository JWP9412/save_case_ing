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

// ---------------------------------------------------------------------------
// 최후 방어선: unhandled rejection / uncaught exception 으로 워커가
// 즉사하지 않게 합니다. (Request is already handled 등)
// 로그만 남기고 프로세스는 유지 → 다음 CASE 또는 WORKER_IDLE 로 복구.
// ---------------------------------------------------------------------------
/**
 * Python 은 stderr=파일/DEVNULL 이라 console.error 만 쓰면 CLI에 안 보입니다.
 * 중요 오류는 stdout(console.log)에도 같이 남겨 캡차 대기 루프가 바로 보게 합니다.
 */
function logVisibleError(prefix, errOrMsg) {
    const msg = (errOrMsg && errOrMsg.message) ? errOrMsg.message : String(errOrMsg || '');
    const line = `${prefix}${msg}`;
    console.log(line);
    console.error(line);
}

process.on('unhandledRejection', (reason) => {
    logVisibleError('⚠️ [Worker] unhandledRejection (프로세스 유지): ', reason);
});
process.on('uncaughtException', (err) => {
    logVisibleError('⚠️ [Worker] uncaughtException (프로세스 유지): ', err);
});

const args = process.argv.slice(2);
const isWorkerMode = args[0] === '--worker';

const rl = readline.createInterface({
    input: process.stdin,
    // output 을 stdout 에 묶으면 파이프 모드에서 버퍼링이 끼어
    // WORKER_READY 가 Python 쪽에 늦게 도착할 수 있습니다.
    terminal: false
});

rl.on('close', () => {
    process.exit(0);
});

/**
 * stdout 한 줄을 즉시 밀어 넣습니다 (파이프 버퍼링 완화).
 * 주니어: console.log 만 쓰면 Windows 파이프에서 READY 가 안 보일 수 있습니다.
 */
function logLine(msg) {
    const line = String(msg == null ? '' : msg);
    try {
        process.stdout.write(line + '\n');
    } catch (_) {
        console.log(line);
    }
}

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
    // 주니어: Python 이 CASEING_COOKIE_DIR(절대경로)를 넘기면 GUI와 동일 프로필을 씁니다.
    // cwd 상대경로만 쓰면 실행 위치에 따라 빈 cookie_data_for_save 가 새로 생깁니다.
    const cookieRoot = (process.env.CASEING_COOKIE_DIR || '').trim()
        || path.join(process.cwd(), 'cookie_data_for_save');
    const userDataDir = path.join(cookieRoot, `instance_${instanceIndex}`);
    await fs.mkdir(userDataDir, { recursive: true }).catch(() => { });

    // 스마트 스킵 진단: Cookies 파일이 있어야 GUI에서 쌓인 세션을 재사용합니다.
    // 최신 Chromium 은 Default/Cookies 대신 Default/Network/Cookies 를 씁니다.
    const cookieCandidates = [
        path.join(userDataDir, 'Default', 'Network', 'Cookies'),
        path.join(userDataDir, 'Default', 'Cookies'),
    ];
    let cookiesHint = 'Cookies 없음(신규·빈 프로필 가능)';
    for (const cookiesPath of cookieCandidates) {
        try {
            const st = await fs.stat(cookiesPath);
            if (st) {
                cookiesHint = `Cookies 있음 (${st.size} bytes, ${path.basename(path.dirname(cookiesPath))}/${path.basename(cookiesPath)})`;
                break;
            }
        } catch (_) {
            // 다음 후보
        }
    }

    console.log(`🚀 [Interactive] Chrome 기동 instance_${instanceIndex}`);
    console.log(`📂 프로필: ${userDataDir}`);
    console.log(`🍪 ${cookiesHint}`);
    const browser = await puppeteer.launch({
        headless: maintenance.browserHeadless,
        userDataDir: userDataDir,
        // CDP 호출이 3분(기본) 끌지 않도록 — 캡차 초기화 30초와 맞춤
        protocolTimeout: 30000,
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
        // 주니어: 접속 직후 body 만 보면 최근검색 DOM 이 없습니다.
        // 검색 폼을 기다린 뒤 몇 초간 다시 스캔합니다.
        console.log(`🔍 [Smart Skip] 최근 검색 내역 확인 중: ${caseNumber}`);
        const formOk = await controller.waitForSearchForm();
        const scan = await controller.scanRecentCase(caseNumber, formOk ? 8000 : 3000);
        foundInRecent = !!scan.found;
        if (foundInRecent) {
            console.log(`✅ [Smart Skip] 최근 검색 내역 발견: ${scan.hint || caseNumber}`);
        } else if (scan.sample) {
            console.log(`ℹ️ [Smart Skip] 목록에 해당 번호 없음 (샘플: ${scan.sample})`);
        } else {
            console.log('ℹ️ [Smart Skip] 최근검색으로 보이는 칸이 없음 (타이밍·미저장·다른 프로필)');
        }
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

        // 워커 QUIT 은 무시하지 않음 — 조회 중지/종료가 먹히게
        if (input.startsWith('{') && input.includes('"cmd"')) {
            try {
                const msg = JSON.parse(input);
                if (msg.cmd === 'QUIT') {
                    console.log('👋 [Interactive] 캡차 대기 중 QUIT — 워커 종료');
                    const err = new Error('WORKER_QUIT');
                    err.code = 'WORKER_QUIT';
                    throw err;
                }
            } catch (e) {
                if (e && e.code === 'WORKER_QUIT') throw e;
            }
            console.log('⚠️ [Interactive] 캡차 대기 중 CASE 수신 — 무시하고 계속 대기');
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

        // dialog 핸들러가 비동기로 플래그를 올리므로 잠깐 기다려 확인
        // (검색 직후 알림이 늦게 뜨면 0건 성공으로 위장되는 사고 방지)
        await new Promise((r) => setTimeout(r, 400));

        if (wrongCaptchaOccurred) {
            console.log('❌ [Interactive] 캡차 불일치 확정 — 진행내용 파싱 중단, 재입력 대기');
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
            // Python 쪽 WRONG_CAPTCHA 재시도·수동 폴백이 이 라인을 감지합니다
            console.log(`WRONG_CAPTCHA_IMAGE: ${filepath}`);
            continue;
        }

        progressData = await controller.extractProgressData(caseNumber);

        // 추출 도중(늦게) 알림이 뜬 경우 — 0건을 성공으로 넘기지 않음
        if (wrongCaptchaOccurred) {
            console.log('❌ [Interactive] 추출 중 캡차 불일치 감지 — 결과 폐기, 재입력 대기');
            const captchaSelector = '#mf_ssgoTopMainTab_contents_content1_body_img_captcha';
            let filepath = '';
            try {
                await page.waitForSelector(captchaSelector, { timeout: 5000 });
                await page.click(captchaSelector);
                await new Promise(r => setTimeout(r, 1500));
                const screenshotsDir = path.join(process.cwd(), 'screenshots');
                await fs.mkdir(screenshotsDir, { recursive: true }).catch(() => {});
                filepath = path.join(
                    screenshotsDir,
                    `${caseNumber}-${Date.now()}-captcha-retry.png`
                );
                const el = await page.$(captchaSelector);
                if (el) await el.screenshot({ path: filepath });
            } catch (e) {
                console.error('⚠️ [Interactive] 늦은 불일치 캡차 갱신 실패:', e.message);
            }
            console.log(`WRONG_CAPTCHA_IMAGE: ${filepath || '(none)'}`);
            continue;
        }

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
        logVisibleError('❌ [Interactive] 오류 발생: ', error);
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

    // 파이프에서도 즉시 보이도록 write (console.log 만으로는 버퍼링될 수 있음)
    logLine(`WORKER_READY instance=${currentInstance}`);

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
                // 프로필이 바뀌면 Chrome 재기동.
                // 같은 레인은 Chrome/페이지를 유지합니다.
                // 주니어: about:blank 로 비우지 않습니다. 최근 검색 UI 가
                // 페이지 메모리에 있어서 blank 후 재접속하면 목록이 비고
                // 스마트 스킵이 매번 실패했습니다.
                // 다음 건은 processOneCase → navigateToSite() 가 검색 URL 로 갑니다.
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
                }

                await processOneCase(page, caseNumber, defendant, court, smartSkipEnabled);
                console.log('WORKER_IDLE');
            } catch (error) {
                if (error && (error.code === 'WORKER_QUIT' || error.message === 'WORKER_QUIT')) {
                    console.log('👋 [Worker] QUIT으로 루프 종료');
                    break;
                }
                // stdout에도 남겨 Python 캡차 대기 루프가 WORKER_IDLE 전에 원인을 보게 함
                logVisibleError('❌ [Interactive] 오류 발생: ', error);
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

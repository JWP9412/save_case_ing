#!/usr/bin/env node
/**
 * 대화형 Puppeteer 실행 스크립트 (Interactive Runner)
 * =================================================
 * 
 * 단일 프로세스로 브라우저를 실행하고, Python과 통신하며 사건 처리를 수행합니다.
 * 브라우저 재연결 없이 세션을 유지하므로 캡차 이미지가 변경되지 않습니다.
 * 
 * 사용법: node src/interactive_runner.js <사건번호> <피고> <법원> [인스턴스번호]
 * 인스턴스번호(0~N): cookie_data_for_save/instance_N 사용. 생략 시 0.
 */

const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs').promises;
const readline = require('readline');
const PageController = require('./PageController');

// 명령행 인수 파싱
const args = process.argv.slice(2);
if (args.length < 3) {
    console.error('사용법: node src/interactive_runner.js <사건번호> <피고> <법원> [인스턴스번호]');
    process.exit(1);
}

const [caseNumber, defendant, court] = args;
const instanceIndex = args.length >= 4 ? parseInt(args[3], 10) || 0 : 0;

// Readline 인터페이스 설정
const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});

rl.on('close', () => {
    process.exit(0);
});

// 한 줄 입력을 기다리는 Promise 함수
function waitForInput() {
    return new Promise((resolve) => {
        rl.once('line', (line) => {
            resolve(line.trim());
        });
    });
}

async function main() {
    let browser = null;
    try {
        console.log(`🚀 [Interactive] 사건 처리 시작: ${caseNumber}`);

        // 1. 브라우저 실행 (전용 차로: cookie_data_for_save/instance_N)
        const userDataDir = path.join(process.cwd(), 'cookie_data_for_save', `instance_${instanceIndex}`);
        await fs.mkdir(userDataDir, { recursive: true }).catch(() => { });

        browser = await puppeteer.launch({
            headless: false, // 캡차 확인을 위해 헤드리스 끔 (필요시 변경 가능)
            userDataDir: userDataDir,
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--window-size=1280,1024',
                '--disable-blink-features=AutomationControlled',
                '--disable-infobars',
                '--remote-debugging-port=0',
                '--disable-dev-shm-usage', // 메모리 부족 방지
                '--disable-gpu' // GPU 가속 비활성화 (안정성 향상)
            ]
        });

        const pages = await browser.pages();
        const page = pages[0];

        // 캡차 오입력 시 재시도용 플래그
        let wrongCaptchaOccurred = false;

        // 알림창 자동 처리 리스너 (자동입력방지 불일치 시 재시도 플래그 설정)
        page.on('dialog', async dialog => {
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
        });

        // PageController 초기화
        const controller = new PageController(page, 'interactive');

        // 2. 사이트 접속
        await controller.navigateToSite();

        // 3. 스마트 스킵 확인 (최근 검색 내역)
        console.log(`🔍 [Smart Skip] 최근 검색 내역 확인 중: ${caseNumber}`);
        const foundInRecent = await page.evaluate((targetNo) => {
            const elements = document.querySelectorAll('a, td');
            for (const el of elements) {
                if (el.textContent.trim() === targetNo) {
                    return true;
                }
            }
            return false;
        }, caseNumber);

        if (foundInRecent) {
            console.log(`✅ [Smart Skip] 최근 검색 내역 발견!`);
            // 스킵 신호 출력 (Python이 이를 감지하고 "CLICK"을 보낼 것임)
            console.log('CAPTCHA_STATUS: SKIP_AND_CLICK');
        } else {
            console.log(`ℹ️ [Smart Skip] 최근 검색 내역 없음 -> 정보 입력 진행`);

            // 4. 정보 입력 및 캡차 캡처
            await controller.selectCourt(court);
            await controller.checkCaseNumberInputMode();
            await controller.checkSaveSearchResult(); // 결과 저장 체크 (중요)
            await controller.inputCaseNumber(caseNumber);
            await controller.inputPartyName(defendant);

            // 캡차 요소가 보일 때까지 대기
            const captchaSelector = '#mf_ssgoTopMainTab_contents_content1_body_img_captcha';
            await page.waitForSelector(captchaSelector, { timeout: 15000 });

            // 스크린샷 저장
            const screenshotsDir = path.join(process.cwd(), 'screenshots');
            await fs.mkdir(screenshotsDir, { recursive: true }).catch(() => { });
            const filename = `${caseNumber}-${Date.now()}-captcha.png`;
            const filepath = path.join(screenshotsDir, filename);

            const element = await page.$(captchaSelector);
            await element.screenshot({ path: filepath });

            console.log(`🖼️ GUI_IMAGE_PATH: ${filepath}`);
        }

        // 5~7. 입력 대기 -> 액션 실행 (캡차 불일치 시 재시도 루프)
        let progressData = null;
        while (true) {
            console.log('⏳ [Interactive] 입력 대기 중...');
            const input = await waitForInput();
            console.log(`📥 [Interactive] 입력 수신: ${input}`);

            if (input === "CLICK") {
                await controller.clickRecentCase(caseNumber);
                progressData = await controller.extractProgressData(caseNumber);
                break;
            }

            wrongCaptchaOccurred = false;
            await controller.inputCaptcha(input);
            await controller.performSearch(input);

            if (wrongCaptchaOccurred) {
                // 캡차 새로고침: 이미지 클릭으로 갱신 시도
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

        // 8. 결과 출력 (JSON)
        const result = {
            caseNumber,
            defendant,
            court,
            progressData,
            success: true,
            timestamp: new Date().toISOString()
        };

        console.log('JSON_RESULT_START');
        console.log(JSON.stringify(result));
        console.log('JSON_RESULT_END');

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

main();

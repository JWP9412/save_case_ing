#!/usr/bin/env node
/**
 * 단일 사건 캡차 이미지 캡처 전용 스크립트
 * ======================================
 * 
 * 사용법: node src/single-case-captcha.js <사건번호>
 * 예시: node src/single-case-captcha.js 2023가합10019
 */

const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs').promises;

// 전역 브라우저 변수 (signal handler에서 접근하기 위해)
let globalBrowser = null;

async function captureCaptchaForCase(caseNumber) {
    let browser = null;

    try {
        console.log(`🔐 캡차 이미지 캡처 시작: ${caseNumber}`);

        // 사용자 데이터 디렉토리 설정 (쿠키 저장용)
        const userDataDir = path.join(process.cwd(), 'user_data', 'captcha_session');

        try {
            // fs.promises를 사용하므로 access로 확인하고 mkdir로 생성
            await fs.access(userDataDir).catch(async () => {
                await fs.mkdir(userDataDir, { recursive: true });
            });
        } catch (e) {
            console.log(`⚠️ 사용자 데이터 디렉토리 생성 실패 (무시됨): ${e.message}`);
        }

        console.log(`📂 사용자 데이터 디렉토리 설정: ${userDataDir}`);

        // 브라우저 실행 (화면에 보이도록 설정)
        browser = await puppeteer.launch({
            headless: false,  // 브라우저를 화면에 표시 (디버깅용)
            devtools: false,
            slowMo: 0,
            userDataDir: userDataDir, // 쿠키 저장을 위한 사용자 데이터 폴더
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--disable-gpu',
                '--disable-dev-shm-usage',
                '--max-old-space-size=4096',  // Node.js 메모리 제한 4GB
                '--js-flags=--max-old-space-size=4096',  // V8 메모리 제한 4GB
                '--disable-dev-shm-usage',  // /dev/shm 사용 안 함 (메모리 문제 방지)
                '--disable-software-rasterizer'  // 소프트웨어 렌더링 비활성화
            ]
        });

        // 전역 변수에 할당 (signal handler에서 접근하기 위해)
        globalBrowser = browser;

        // 기존 about:blank 페이지 사용 (새 페이지 생성 안 함!)
        const pages = await browser.pages();
        const page = pages[0]; // 브라우저 시작 시 자동 생성된 페이지 사용
        console.log(`✅ 기존 페이지 사용: ${page.url()}`);

        // 스크린샷 디렉토리 생성
        const screenshotsDir = path.join(process.cwd(), 'screenshots');
        await fs.mkdir(screenshotsDir, { recursive: true });

        // 대법원 사이트 접속
        console.log('🌐 대법원 사이트 접속 중...');
        await page.goto('https://ssgo.scourt.go.kr/ssgo/index.on?cortId=www', {
            waitUntil: 'networkidle2',
            timeout: 60000  // 60초로 증가 (네트워크 지연 고려)
        });

        // 사건번호입력모드 체크박스 클릭
        console.log('📋 [DEBUG] 사건번호입력모드 체크박스 처리 시작...');
        const checkboxSelector = '#mf_ssgoTopMainTab_contents_content1_body_cbx_chkSanoInputMode_input_0';
        try {
            await page.waitForSelector(checkboxSelector, { timeout: 10000 });
            console.log('✅ [DEBUG] 사건번호입력모드 체크박스 발견');

            const isChecked = await page.$eval(checkboxSelector, el => el.checked);
            console.log(`📋 [DEBUG] 사건번호입력모드 현재 상태: ${isChecked}`);

            if (!isChecked) {
                console.log('🖱️ [DEBUG] 사건번호입력모드 클릭 시도...');
                await page.click(checkboxSelector);
                console.log('✅ [DEBUG] 사건번호입력모드 클릭 완료');
            } else {
                console.log('ℹ️ [DEBUG] 사건번호입력모드 이미 체크됨');
            }
        } catch (e) {
            console.error(`❌ [ERROR] 사건번호입력모드 체크박스 처리 실패: ${e.message}`);
        }

        // 💾 사건검색 결과 저장 체크박스 처리 (추가)
        console.log('💾 [DEBUG] 사건검색 결과 저장 체크박스 처리 시작...');
        const saveResultSelector = '#mf_ssgoTopMainTab_contents_content1_body_cbx_saveCsRsltYn_input_0';

        try {
            console.log(`🔍 [DEBUG] 결과저장 체크박스 찾는 중... (${saveResultSelector})`);
            await page.waitForSelector(saveResultSelector, { timeout: 5000 });
            console.log('✅ [DEBUG] 결과저장 체크박스 발견');

            const isResultChecked = await page.$eval(saveResultSelector, el => el.checked);
            console.log(`📋 [DEBUG] 결과저장 현재 상태: ${isResultChecked}`);

            if (!isResultChecked) {
                // 검증된 클릭 방식 (단순 클릭 -> 확인 -> JS)
                console.log('🖱️ [DEBUG] 결과저장 클릭 시도 (page.click)...');
                await page.click(saveResultSelector);
                await page.waitForTimeout(500);

                const newResultChecked = await page.$eval(saveResultSelector, el => el.checked);
                console.log(`📋 [DEBUG] 클릭 후 상태: ${newResultChecked}`);

                if (!newResultChecked) {
                    console.log('⚠️ [DEBUG] 클릭 실패, JS 강제 실행 시도...');
                    await page.evaluate((selector) => {
                        const checkbox = document.querySelector(selector);
                        if (checkbox) {
                            checkbox.checked = true;
                            checkbox.dispatchEvent(new Event('change', { bubbles: true }));
                            console.log('⚡ [INTERNAL] JS로 checked=true 설정 및 이벤트 발송');
                        } else {
                            console.log('❌ [INTERNAL] JS 실행 중 요소를 찾을 수 없음');
                        }
                    }, saveResultSelector);
                    console.log('✅ [DEBUG] JS 강제 실행 완료');
                } else {
                    console.log('✅ [DEBUG] 클릭으로 체크 성공');
                }
                console.log('✅ [DEBUG] 사건검색 결과 저장 체크 로직 종료');
            } else {
                console.log('✅ [DEBUG] 이미 사건검색 결과 저장 체크됨');
            }
        } catch (e) {
            console.log(`⚠️ [WARN] 사건검색 결과 저장 체크박스 처리 실패 (무시하고 진행): ${e.message}`);
        }

        // 법원 선택 (명령행 인자에서 받기)
        const court = process.argv[4];  // 4번째 인자 (0:node, 1:script, 2:caseNumber, 3:defendant, 4:court)

        if (!court) {
            throw new Error('법원 정보가 필요합니다. 사용법: node src/single-case-captcha.js <사건번호> <피고> <법원>');
        }

        console.log(`🏛️ 법원 선택 중: ${court}`);

        const courtSelector = '#mf_ssgoTopMainTab_contents_content1_body_sbx_cortCd';
        await page.waitForSelector(courtSelector, { timeout: 10000 });

        // 법원 옵션들 가져오기
        const courtOptions = await page.evaluate((selector) => {
            const element = document.querySelector(selector);
            const options = Array.from(element.options);
            return options.map(opt => opt.text);
        }, courtSelector);

        // 법원명이 포함된 옵션의 인덱스 찾기 (정확한 매칭 우선)
        let courtIndex = courtOptions.findIndex(opt => opt === court);

        // 정확한 매칭이 없으면 부분 매칭 시도
        if (courtIndex === -1) {
            courtIndex = courtOptions.findIndex(opt => opt.includes(court));
        }

        if (courtIndex === -1) {
            throw new Error(`법원을 찾을 수 없습니다: ${court}`);
        }

        console.log(`🔍 법원 검색 결과: ${court} → 인덱스 ${courtIndex}`);

        // 법원 선택
        await page.evaluate((selector, index) => {
            const element = document.querySelector(selector);
            element.selectedIndex = index;
            element.dispatchEvent(new Event('change', { bubbles: true }));
            element.dispatchEvent(new Event('input', { bubbles: true }));
        }, courtSelector, courtIndex);

        console.log(`✅ 법원 선택 완료: ${court}`);

        // 사건번호 입력
        console.log(`📝 사건번호 입력 중: ${caseNumber}`);
        const caseNumberSelector = '#mf_ssgoTopMainTab_contents_content1_body_ibx_fullCsNo';
        await page.waitForSelector(caseNumberSelector, { timeout: 10000 });

        await page.evaluate((selector, text) => {
            const element = document.querySelector(selector);
            element.focus();
            element.value = text;
            element.dispatchEvent(new Event('input', { bubbles: true }));
            element.dispatchEvent(new Event('change', { bubbles: true }));
        }, caseNumberSelector, caseNumber);

        console.log('✅ 사건번호 입력 완료');

        // 당사자명 입력 (실제 피고명)
        console.log('👤 당사자명 입력 중...');
        const partyNameSelector = '#mf_ssgoTopMainTab_contents_content1_body_ibx_btprNm';
        await page.waitForSelector(partyNameSelector, { timeout: 10000 });

        // 피고명을 명령행 인수에서 받기
        const defendant = process.argv[3] || '테스트';

        await page.evaluate((selector, text) => {
            const element = document.querySelector(selector);
            element.focus();
            element.value = text;
            element.dispatchEvent(new Event('input', { bubbles: true }));
            element.dispatchEvent(new Event('change', { bubbles: true }));
        }, partyNameSelector, defendant);

        console.log('✅ 당사자명 입력 완료');

        // 캡차 이미지 캡처
        console.log('🔐 캡차 이미지 캡처 중...');
        const captchaSelector = '#mf_ssgoTopMainTab_contents_content1_body_img_captcha';
        await page.waitForSelector(captchaSelector, { timeout: 30000 });  // 30초로 증가

        // 요소가 화면에 보이는지 확인
        const element = await page.$(captchaSelector);
        const isVisible = await element.isIntersectingViewport();

        if (!isVisible) {
            await element.scrollIntoView();
            await page.waitForTimeout(1000);
        }

        // 요소 크기 확인
        const boundingBox = await element.boundingBox();
        console.log(`📏 캡차 요소 크기: ${JSON.stringify(boundingBox)}`);

        if (!boundingBox || boundingBox.width === 0 || boundingBox.height === 0) {
            throw new Error('캡차 요소 크기가 0입니다');
        }

        // 캡차 이미지 캡처
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
        const filename = `${caseNumber}-${timestamp}-captcha.png`;
        const filepath = path.join(screenshotsDir, filename);

        await element.screenshot({
            path: filepath,
            type: 'png'
        });

        // 파일 생성 확인
        const stats = await fs.stat(filepath);
        console.log(`📸 캡차 이미지 캡처 완료: ${filename} (${stats.size} bytes)`);

        // GUI에 즉시 전달하기 위해 이미지 경로 출력
        console.log(`🖼️ GUI_IMAGE_PATH: ${filepath}`);

        // 브라우저 WebSocket URL 출력 (재연결용)
        const wsEndpoint = browser.wsEndpoint();
        console.log(`🔗 BROWSER_WS_URL: ${wsEndpoint}`);
        console.log(`📸 캡차 이미지 캡처 완료 - 브라우저 유지 중`);

        return filepath;

    } catch (error) {
        console.error(`❌ 캡차 이미지 캡처 실패: ${error.message}`);
        console.error(`❌ 에러 스택: ${error.stack}`);
        console.error(`❌ 사건번호: ${caseNumber}`);
        throw error;
    } finally {
        // 브라우저를 종료하지 않고 유지
        console.log('🔒 브라우저 유지 (캡차 입력 대기)');
        console.log('🌐 브라우저 상태: 활성화됨');
        console.log('⏳ 사용자 캡차 입력 대기 중...');
    }
}

// 명령행 인수 처리
async function main() {
    const caseNumber = process.argv[2];

    if (!caseNumber) {
        console.error('❌ 사용법: node src/single-case-captcha.js <사건번호>');
        process.exit(1);
    }

    try {
        const imagePath = await captureCaptchaForCase(caseNumber);
        console.log(`✅ 성공: ${imagePath}`);

        // 이미지 경로 출력 후 브라우저 유지
        console.log('⏳ 브라우저 유지 중... (사용자 입력 대기)');
        console.log('🌐 브라우저 상태: 활성화됨 (종료되지 않음)');
        console.log('👤 사용자가 브라우저에서 직접 캡차 입력 가능');

        // 브라우저를 유지하면서 무한 대기 + keepalive 메시지
        setInterval(() => {
            console.log('KEEPALIVE'); // Python이 프로세스가 살아있는지 확인용
        }, 2000); // 2초마다 (연결 유지 강화)

        await new Promise(() => { }); // 무한 대기
    } catch (error) {
        console.error(`❌ 실패: ${error.message}`);
        // process.exit(1); // 브라우저를 종료하지 않음
        console.log('🔒 브라우저 유지 (오류 발생)');
    }
}

// Signal handler: 프로세스 종료 시 브라우저도 함께 종료
process.on('SIGTERM', async () => {
    console.log('🔄 SIGTERM 수신 - 브라우저 종료 중...');
    if (globalBrowser) {
        try {
            await globalBrowser.close();
            console.log('✅ 브라우저 종료 완료');
        } catch (error) {
            console.error('❌ 브라우저 종료 실패:', error.message);
        }
    }
    process.exit(0);
});

process.on('SIGINT', async () => {
    console.log('🔄 SIGINT 수신 - 브라우저 종료 중...');
    if (globalBrowser) {
        try {
            await globalBrowser.close();
            console.log('✅ 브라우저 종료 완료');
        } catch (error) {
            console.error('❌ 브라우저 종료 실패:', error.message);
        }
    }
    process.exit(0);
});

if (require.main === module) {
    main();
}

module.exports = { captureCaptchaForCase };

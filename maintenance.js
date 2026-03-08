/**
 * 유지보수용 설정 (Node/Puppeteer 쪽)
 * - src/interactive_runner.js, src/single-case-captcha.js 에서 require 함.
 * - browserHeadless: true → 브라우저 창 숨김(기본). 디버깅 시 false 로 바꾸면 창이 보임.
 */
module.exports = {
    browserHeadless: true,
};

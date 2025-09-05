const { defineConfig } = require("cypress");

module.exports = defineConfig({
  fixturesFolder: "cypress/fixtures",
  chromeWebSecurity: false,
  retries: 0,  // 재시도 0번으로 설정
  responseTimeout: 300000,
  video: true,  // 비디오 녹화 활성화 - 캡차 처리 확인용
  e2e: {
    supportFile: false,
  },
});

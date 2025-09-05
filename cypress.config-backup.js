const { defineConfig } = require("cypress");

module.exports = defineConfig({
  fixturesFolder: "cypress/fixtures",
  chromeWebSecurity: false,
  retries: 0,  // 재시도 0번으로 설정
  responseTimeout: 300000,
  video: false,  // 비디오 녹화 비활성화 - 불필요함
  e2e: {
    supportFile: false,
  },
});

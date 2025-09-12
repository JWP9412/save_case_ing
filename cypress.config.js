/**
 * Cypress 설정 파일
 * ==================
 * 
 * 역할: Cypress 테스트 프레임워크의 전역 설정을 정의
 * 기능:
 * - 테스트 데이터 폴더 경로 설정
 * - 브라우저 보안 설정 (캡차 처리용)
 * - 타임아웃 및 재시도 설정
 * - 비디오 녹화 활성화 (디버깅용)
 * 
 * 주요 설정:
 * - fixturesFolder: 테스트 데이터 위치
 * - chromeWebSecurity: false (캡차 처리용)
 * - responseTimeout: 5분 (긴 처리 시간 대응)
 * - video: true (실행 과정 녹화)
 */

const { defineConfig } = require("cypress");

module.exports = defineConfig({
  fixturesFolder: "cypress/fixtures",  // 테스트 데이터 폴더
  chromeWebSecurity: false,            // 브라우저 보안 비활성화 (캡차 처리용)
  retries: 0,                          // 재시도 0번으로 설정
  responseTimeout: 300000,             // 5분 타임아웃 (캡차 처리 시간 고려)
  video: true,                         // 비디오 녹화 활성화 - 캡차 처리 확인용
  e2e: {
    supportFile: false,                // 지원 파일 비활성화
  },
});

/**
 * Puppeteer 설정 파일
 * =====================
 *
 * 주니어 개발자 참고:
 * - Puppeteer v19+ 는 Chrome을 node_modules가 아니라
 *   사용자 홈 폴더(~/.cache/puppeteer)에 내려받습니다.
 * - 그러면 포터블 배포(폴더 통째로 복사) 시 Chrome이 빠져서
 *   다른 PC에서 "Could not find Chrome" 오류가 납니다.
 * - 그래서 캐시 위치를 프로젝트 안 runtime/puppeteer 로 고정합니다.
 *   → 빌드 스크립트가 이 폴더를 배포 폴더에 그대로 복사하면
 *     다른 PC에서도 Chrome이 함께 따라갑니다.
 *
 * 주의: 이 파일은 Node 프로세스의 cwd(=BASE_DIR) 기준으로 탐색되므로
 *       포터블 폴더 루트에도 복사돼야 합니다. (build_portable.ps1이 처리)
 */
const { join } = require('path');

module.exports = {
  // __dirname = 이 파일이 있는 폴더 (프로젝트 루트 / 포터블 루트)
  cacheDirectory: join(__dirname, 'runtime', 'puppeteer'),
};

#!/usr/bin/env node
/**
 * 일반내용 DOM 조사 도우미 (1단계)
 * =================================
 *
 * 사용법 (개발자용):
 *   1) maintenance.js 의 browserHeadless 를 false 로 잠시 바꿉니다.
 *   2) 평소처럼 CaseIng에서 사건 1건을 조회합니다.
 *   3) 이 스크립트는 실제 크롤링 경로에 심지 않고,
 *      PageController.extractGeneralInfo 가 쓰는 텍스트 기반 파싱 전략을
 *      문서화·검증하기 위한 참고용입니다.
 *
 * 실측 결론 (사용자 제공 사진1~3 + WebSquare ID 패턴):
 * - 진행내용 탭(ssgoTab2) 클릭 전 화면 = 일반내용
 * - 같은 화면에 이미 존재: 기본내용, 최근기일내용, 최근 제출서류,
 *   당사자내용, 대리인내용 (추가 클릭/로딩 불필요 → 비용 0)
 * - 탭 body 추정 ID:
 *   #mf_ssgoTopMainTab_contents_content1_body_wfSsgoDetail_ssgoCsDetailTab_contents_ssgoTab1_body
 * - 표 파싱은 ID보다 제목 텍스트("기본내용","최근기일","제출서류","당사자내용","대리인내용")
 *   기준으로 찾는 편이 사이트 개편에 강합니다.
 *
 * 자동 수집 범위 확정:
 * - 평소 조회 시: basic + recent_hearings + recent_documents + parties + attorneys 전부 저장
 * - 돋보기 창의 "당사자·대리인 내용 변경시 클릭": 최신화가 필요할 때 재조회
 */

console.log(`
[inspect_general_info_dom]
실측 결론 요약:
  - 일반내용은 진행내용 탭 클릭 직전 DOM에 이미 렌더됨
  - 당사자/대리인 표도 같은 화면에 존재 (추가 클릭 불필요)
  - 따라서 평소 조회 때 전부 저장해도 추가 비용 없음
  - 파싱은 제목 텍스트 기반 + ssgoTab1_body 스코프 우선
`);

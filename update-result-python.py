#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cypress 테스트 결과를 구글시트에 업데이트하는 스크립트
"""

import gspread
import os
from datetime import datetime

SPREADSHEET_ID = '1ShaDTz4pj8SRWvf3ahcVI-gStYK-dFSBPsS6BnDOFzU'

def update_test_result():
    try:
        print('🔍 구글 스프레드시트 연결 중...')
        
        # 구글 시트 연결
        gc = gspread.service_account(filename='./api/certification/service-account.json')
        doc = gc.open_by_key(SPREADSHEET_ID)
        
        # 첫 번째 워크시트 (사건 진행현황)
        worksheet = doc.get_worksheet(0)
        
        print('📊 사건 진행현황 시트에 결과 업데이트 중...')
        
        # 현재 날짜
        today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 테스트 결과 데이터
        court = "서울중앙지방법원"
        case_number = "2024가합51101"
        manager = "신안"
        
        # 스크린샷 파일 확인
        screenshot_path = './cypress/screenshots/final-case-ing.cy.js/2024__51101.png'
        screenshot_exists = os.path.exists(screenshot_path)
        
        if screenshot_exists:
            result = "검색 성공 ✅"
            image_link = f"로컬 저장: {screenshot_path}"
        else:
            result = "검색 실패 ❌"
            image_link = "스크린샷 없음"
        
        # 2번째 행에 결과 업데이트 (A2:F2)
        values = [[
            court,           # A열: 법원
            case_number,     # B열: 사건번호  
            manager,         # C열: 당사자명
            result,          # D열: 결과
            today,           # E열: 처리일시
            image_link       # F열: 스크린샷 경로
        ]]
        
        worksheet.update('A2:F2', values)
        
        print('✅ 구글시트 업데이트 완료!')
        print(f'📋 업데이트 내용:')
        print(f'   법원: {court}')
        print(f'   사건번호: {case_number}')
        print(f'   당사자: {manager}')
        print(f'   결과: {result}')
        print(f'   처리일시: {today}')
        print(f'   스크린샷: {image_link}')
        
        return True
        
    except FileNotFoundError:
        print('❌ service-account.json 파일을 찾을 수 없습니다.')
        return False
        
    except Exception as e:
        print(f'❌ 오류 발생: {e}')
        return False

if __name__ == "__main__":
    print('🚀 Cypress 테스트 결과 구글시트 업데이트 시작\n')
    success = update_test_result()
    
    if success:
        print('\n🎉 구글시트 업데이트 성공!')
    else:
        print('\n💔 구글시트 업데이트 실패')
        
    print('\n' + '='*50)




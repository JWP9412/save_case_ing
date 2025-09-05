#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
구글 스프레드시트 읽기/쓰기 테스트
"""

import gspread
from datetime import datetime

def test_sheet_operations():
    try:
        print("🔍 구글 서비스 계정 인증 중...")
        gc = gspread.service_account(filename='./certification/service-account.json')
        
        # 스프레드시트 열기
        sheet_id = "1ShaDTz4pj8SRWvf3ahcVI-gStYK-dFSBPsS6BnDOFzU"
        doc = gc.open_by_key(sheet_id)
        worksheet = doc.sheet1  # 첫 번째 시트
        
        print(f"✅ 스프레드시트 열기 성공: {doc.title}")
        
        # 테스트 데이터 쓰기
        print("\n📝 테스트 데이터 쓰기 중...")
        test_data = [
            ["테스트", "항목", "시간"],
            ["case-ing", "API 테스트", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            ["구글", "스프레드시트", "연동 성공! 🎉"]
        ]
        
        # A1부터 데이터 쓰기
        worksheet.update('A1:C3', test_data)
        print("✅ 데이터 쓰기 성공!")
        
        # 데이터 읽기
        print("\n📖 데이터 읽기 중...")
        all_data = worksheet.get_all_values()
        
        print("📊 읽어온 데이터:")
        for i, row in enumerate(all_data, 1):
            print(f"  {i}행: {row}")
            
        return True
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False

if __name__ == "__main__":
    print("🚀 구글 스프레드시트 읽기/쓰기 테스트 시작\n")
    success = test_sheet_operations()
    
    if success:
        print("\n🎉 구글 스프레드시트 연동 완전 성공!")
        print("💡 이제 case-ing 프로젝트에서 사용할 수 있습니다!")
    else:
        print("\n💔 테스트 실패")
        
    print("\n" + "="*60)


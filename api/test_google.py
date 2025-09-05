
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
구글 스프레드시트 연동 테스트 스크립트
"""

import gspread
import sys

def test_google_sheets():
    try:
        print("🔍 구글 서비스 계정 인증 중...")
        gc = gspread.service_account(filename='./certification/service-account.json')
        print("✅ 인증 성공!")
        
        print("\n📊 사용 가능한 스프레드시트 목록:")
        sheets = gc.openall()
        
        if not sheets:
            print("❌ 접근 가능한 스프레드시트가 없습니다.")
            print("💡 해결 방법:")
            print("1. 구글 시트를 생성하세요")
            print("2. 서비스 계정 이메일에 편집 권한을 주세요")
            return False
            
        for i, sheet in enumerate(sheets, 1):
            print(f"  {i}. {sheet.title} (ID: {sheet.id})")
            
        return True
        
    except FileNotFoundError:
        print("❌ service-account.json 파일을 찾을 수 없습니다.")
        print("📁 파일 위치: ./certification/service-account.json")
        return False
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False

if __name__ == "__main__":
    print("🚀 구글 스프레드시트 연동 테스트 시작\n")
    success = test_google_sheets()
    
    if success:
        print("\n🎉 구글 API 연동 성공!")
    else:
        print("\n💔 구글 API 연동 실패")
        
    print("\n" + "="*50)


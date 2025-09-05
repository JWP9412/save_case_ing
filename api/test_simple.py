#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
간단한 구글 인증 테스트
"""

import gspread
import json

def test_service_account():
    try:
        print("🔍 서비스 계정 파일 확인 중...")
        
        # 파일 존재 확인
        with open('./certification/service-account.json', 'r') as f:
            service_account_info = json.load(f)
            
        print("✅ service-account.json 파일 읽기 성공!")
        print(f"📧 서비스 계정 이메일: {service_account_info.get('client_email', 'N/A')}")
        print(f"🆔 프로젝트 ID: {service_account_info.get('project_id', 'N/A')}")
        
        print("\n🔗 구글 인증 객체 생성 중...")
        gc = gspread.service_account(filename='./certification/service-account.json')
        print("✅ 구글 인증 객체 생성 성공!")
        
        return True
        
    except FileNotFoundError:
        print("❌ service-account.json 파일을 찾을 수 없습니다.")
        return False
        
    except json.JSONDecodeError:
        print("❌ service-account.json 파일이 유효한 JSON이 아닙니다.")
        return False
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False

if __name__ == "__main__":
    print("🚀 구글 서비스 계정 테스트 시작\n")
    success = test_service_account()
    
    if success:
        print("\n🎉 기본 설정 완료!")
        print("💡 다음 단계: Google Drive API 활성화 필요")
    else:
        print("\n💔 기본 설정 실패")
        
    print("\n" + "="*50)


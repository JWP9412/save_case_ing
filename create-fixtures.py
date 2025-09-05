#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
구글 시트에서 직접 데이터를 읽어서 Cypress fixtures 생성
"""

import gspread
import json
import os

SPREADSHEET_ID = '1ShaDTz4pj8SRWvf3ahcVI-gStYK-dFSBPsS6BnDOFzU'
FIXTURE_FOLDER = './cypress/fixtures'

def chunk_array(array, chunk_size):
    """배열을 청크 단위로 분할"""
    for i in range(0, len(array), chunk_size):
        yield array[i:i + chunk_size]

def create_fixtures_from_sheet():
    try:
        print("🔍 구글 스프레드시트 인증 중...")
        gc = gspread.service_account(filename='./api/certification/service-account.json')
        
        print("📊 스프레드시트 열기...")
        doc = gc.open_by_key(SPREADSHEET_ID)
        
        # 두 번째 시트에서 사건 목록 읽기 (첫 번째는 결과, 두 번째는 입력)
        try:
            worksheet = doc.get_worksheet(1)  # 두 번째 시트
            print("✅ 사건 목록 시트에서 데이터 읽기...")
        except:
            worksheet = doc.sheet1  # 첫 번째 시트 사용
            print("⚠️ 첫 번째 시트에서 데이터 읽기...")
        
        # 데이터 읽기
        all_data = worksheet.get_all_values()
        
        if len(all_data) <= 1:  # 헤더만 있거나 빈 시트
            print("⚠️ 시트가 비어있습니다. 테스트 데이터를 사용합니다.")
            cases_data = [
                [2, "서울중앙지방법원", "2024가단1234", "김철수"],
                [3, "서울남부지방법원", "2024가단5678", "이영희"],
                [4, "인천지방법원", "2024가단9012", "박민수"]
            ]
        else:
            # 헤더 제외하고 데이터 가져오기
            cases_data = []
            for i, row in enumerate(all_data[1:], 2):  # 2번째 행부터 시작
                if len(row) >= 3 and row[0] and row[1]:  # 법원, 사건번호가 있는 경우
                    court = row[0] if len(row) > 0 else ""
                    case_number = row[1] if len(row) > 1 else ""
                    manager = row[2] if len(row) > 2 else "담당자"
                    cases_data.append([i, court, case_number, manager])
        
        print(f"📋 {len(cases_data)}개의 사건 데이터 발견")
        
        # fixtures 폴더 생성
        if not os.path.exists(FIXTURE_FOLDER):
            os.makedirs(FIXTURE_FOLDER)
        
        # 5개씩 청크로 분할
        chunks = list(chunk_array(cases_data, 5))
        
        for i, chunk in enumerate(chunks):
            file_path = f"{FIXTURE_FOLDER}/cases_chunk_{i}.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(chunk, f, ensure_ascii=False, indent=2)
            print(f"✅ 생성됨: {file_path} ({len(chunk)}개 사건)")
        
        print("🎉 픽스쳐 생성 완료!")
        return True
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False

if __name__ == "__main__":
    print("🚀 구글 시트 → Cypress 픽스쳐 생성 시작\n")
    success = create_fixtures_from_sheet()
    
    if success:
        print("\n💡 이제 Cypress 테스트를 실행할 수 있습니다!")
        print("명령어: npm run test")
    else:
        print("\n💔 픽스쳐 생성 실패")
        
    print("\n" + "="*60)

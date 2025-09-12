#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
구글시트 데이터 생성기 - 파이썬 버전
=====================================

역할: 구글 스프레드시트에서 사건 데이터를 읽어와서 Cypress 테스트용 fixtures 생성
기능:
- 구글 스프레드시트 연결 및 데이터 읽기
- 사건 데이터를 5개씩 청크로 나누기
- JSON 파일로 변환하여 cypress/fixtures/ 폴더에 저장
- Cypress 병렬 실행을 위한 데이터 준비

사용법: python create-fixtures-python.py
"""

import gspread
import json
import os

FIXTURE_FOLDER_PATH = './cypress/fixtures'
SPREADSHEET_ID = '1ShaDTz4pj8SRWvf3ahcVI-gStYK-dFSBPsS6BnDOFzU'

def chunk_array(array, chunk_size):
    """배열을 chunk_size 단위로 나누기"""
    chunks = []
    for i in range(0, len(array), chunk_size):
        chunks.append(array[i:i + chunk_size])
    return chunks

def create_fixtures():
    try:
        print('🔍 구글 스프레드시트에서 직접 데이터 가져오는 중...')
        
        # 구글 시트 연결
        gc = gspread.service_account(filename='./api/certification/service-account.json')
        doc = gc.open_by_key(SPREADSHEET_ID)
        
        # 두 번째 워크시트 (사건 목록)
        worksheet = doc.get_worksheet(1)
        list_of_lists = worksheet.get_values()
        
        print(f'📊 구글시트에서 {len(list_of_lists)}개 행 읽기 완료')
        
        # 헤더 제외하고 행 번호 추가
        indexed_array = []
        for i, row in enumerate(list_of_lists[1:], start=2):  # 2번째 행부터
            if len(row) >= 3 and row[0] and row[1] and row[2]:  # 빈 행 제외
                indexed_row = [i] + row
                indexed_array.append(indexed_row)
        
        print(f'✅ 유효한 데이터: {len(indexed_array)}개')
        
        # fixtures 폴더 생성
        if not os.path.exists(FIXTURE_FOLDER_PATH):
            os.makedirs(FIXTURE_FOLDER_PATH)
        
        # 5개씩 청크로 나누기
        chunks = chunk_array(indexed_array, 5)
        
        for i, chunk in enumerate(chunks):
            file_path = f'{FIXTURE_FOLDER_PATH}/cases_chunk_{i}.json'
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(chunk, f, ensure_ascii=False, indent=2)
            print(f'✅ 생성됨: {file_path}')
            
            # 생성된 파일 내용 확인
            print(f'📋 {file_path} 내용:')
            with open(file_path, 'r', encoding='utf-8') as f:
                print(f.read()[:200] + '...' if len(f.read()) > 200 else f.read())
        
        print('🎉 Cypress fixtures 생성 완료!')
        
        # 첫 번째 청크 내용 미리보기
        if chunks:
            print(f'📋 첫 번째 청크 미리보기:')
            for row in chunks[0][:3]:
                print(f'   행 {row[0]}: {row[1]} {row[2]} ({row[3]})')
        
    except FileNotFoundError:
        print('❌ service-account.json 파일을 찾을 수 없습니다.')
        print('📁 파일 위치: ./api/certification/service-account.json')
        
    except Exception as e:
        print(f'❌ 오류 발생: {e}')

if __name__ == "__main__":
    print('🚀 구글시트 직접 연동 fixtures 생성 시작\n')
    create_fixtures()
    print('\n' + '='*50)

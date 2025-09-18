#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
진행내용 그리드 데이터 추출 및 구글 시트 저장 스크립트
====================================================

역할: Cypress에서 추출한 진행내용 그리드 데이터를 구글 시트의 새로운 탭에 저장
기능:
- JSON 파일에서 진행내용 데이터 읽기
- 구글 시트에 새로운 워크시트 생성
- 테이블 형태로 데이터 저장

사용법: py progress-extractor.py [사건번호]
"""

import json
import gspread
from google.oauth2.service_account import Credentials
import sys
from datetime import datetime
import os

def load_progress_data(case_number):
    """진행내용 데이터 JSON 파일을 읽어옵니다."""
    try:
        filename = f"progress_data_{case_number}.json"
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"[INFO] 진행내용 데이터 로드 완료: {filename}")
            return data
        else:
            print(f"[ERROR] 파일을 찾을 수 없습니다: {filename}")
            return None
    except Exception as e:
        print(f"[ERROR] 데이터 로드 실패: {e}")
        return None

def connect_to_google_sheets():
    """구글 시트에 연결합니다."""
    try:
        # 서비스 계정 키 파일 경로 (기존 설정과 동일)
        credentials_file = "./api/certification/service-account.json"
        
        if not os.path.exists(credentials_file):
            print(f"[ERROR] 서비스 계정 키 파일을 찾을 수 없습니다: {credentials_file}")
            return None
        
        # 기존 설정과 동일한 방식으로 연결
        gc = gspread.service_account(filename=credentials_file)
        
        # 기존 스프레드시트 ID 사용
        spreadsheet_id = "1ShaDTz4pj8SRWvf3ahcVI-gStYK-dFSBPsS6BnDOFzU"
        spreadsheet = gc.open_by_key(spreadsheet_id)
        
        print("[INFO] 구글 시트 연결 성공")
        return spreadsheet
        
    except Exception as e:
        print(f"[ERROR] 구글 시트 연결 실패: {e}")
        return None

def create_progress_worksheet(spreadsheet, case_number):
    """진행내용 전용 워크시트를 생성합니다."""
    try:
        worksheet_name = f"진행내용_{case_number}"
        
        # 기존 워크시트가 있는지 확인
        try:
            worksheet = spreadsheet.worksheet(worksheet_name)
            print(f"[INFO] 기존 워크시트 사용: {worksheet_name}")
        except gspread.WorksheetNotFound:
            # 새 워크시트 생성
            worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows=1000, cols=10)
            print(f"[INFO] 새 워크시트 생성: {worksheet_name}")
        
        return worksheet
        
    except Exception as e:
        print(f"[ERROR] 워크시트 생성 실패: {e}")
        return None

def save_progress_data(worksheet, progress_data, case_number):
    """진행내용 데이터를 구글 시트에 저장합니다."""
    try:
        if not progress_data or 'rows' not in progress_data:
            print("[ERROR] 유효한 진행내용 데이터가 없습니다")
            return False
        
        # 헤더 설정
        headers = ['일자', '내용', '결과', '공시문']
        worksheet.update('A1:D1', [headers])
        
        # 데이터 행들 저장
        rows = progress_data['rows']
        if rows:
            # 각 행의 데이터를 리스트로 변환
            data_rows = []
            for row in rows:
                data_row = [
                    row.get('date', ''),
                    row.get('content', ''),
                    row.get('result', ''),
                    row.get('document', '')
                ]
                data_rows.append(data_row)
            
            # 데이터를 시트에 업데이트 (A2부터 시작)
            if data_rows:
                worksheet.update(f'A2:D{len(data_rows) + 1}', data_rows)
                print(f"[INFO] {len(data_rows)}개 행의 진행내용 데이터 저장 완료")
        
        # 메타데이터 추가
        metadata_row = len(data_rows) + 3
        worksheet.update(f'A{metadata_row}:D{metadata_row}', [
            ['사건번호', case_number, '저장일시', datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
        ])
        
        print(f"[SUCCESS] 진행내용 데이터가 구글 시트에 저장되었습니다")
        return True
        
    except Exception as e:
        print(f"[ERROR] 데이터 저장 실패: {e}")
        return False

def main():
    """메인 함수"""
    print("=== 진행내용 그리드 데이터 추출기 ===")
    
    # 명령행 인수에서 사건번호 가져오기
    if len(sys.argv) > 1:
        case_number = sys.argv[1]
    else:
        case_number = "TEST_CASE"
        print(f"[INFO] 사건번호가 제공되지 않아 기본값 사용: {case_number}")
    
    print(f"[INFO] 처리할 사건번호: {case_number}")
    
    # 1. 진행내용 데이터 로드
    progress_data = load_progress_data(case_number)
    if not progress_data:
        print("[ERROR] 진행내용 데이터를 로드할 수 없습니다")
        return
    
    # 2. 구글 시트 연결
    spreadsheet = connect_to_google_sheets()
    if not spreadsheet:
        print("[ERROR] 구글 시트에 연결할 수 없습니다")
        return
    
    # 3. 진행내용 워크시트 생성
    worksheet = create_progress_worksheet(spreadsheet, case_number)
    if not worksheet:
        print("[ERROR] 워크시트를 생성할 수 없습니다")
        return
    
    # 4. 데이터 저장
    success = save_progress_data(worksheet, progress_data, case_number)
    if success:
        print("[SUCCESS] 모든 작업이 완료되었습니다!")
    else:
        print("[ERROR] 데이터 저장에 실패했습니다")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Puppeteer 결과 데이터를 구글 시트에 저장하는 스크립트
====================================================

역할: Puppeteer에서 생성된 case_result_*.json 파일을 구글 시트에 저장
기능:
- results/ 폴더에서 case_result_*.json 파일 읽기
- 구글 시트에 새로운 워크시트 생성
- 진행내용 데이터를 테이블 형태로 저장

사용법: 
- py puppeteer-to-sheets.py [사건번호]  # 특정 사건만
- py puppeteer-to-sheets.py --all      # 모든 사건
"""

import json
import gspread
from google.oauth2.service_account import Credentials
import sys
import os
import glob
from datetime import datetime

def load_puppeteer_result(case_number=None):
    """Puppeteer 결과 JSON 파일을 읽어옵니다."""
    try:
        if case_number:
            # 특정 사건번호의 파일 찾기 (패턴 매칭 사용)
            pattern = f"results/case_result_*{case_number}*.json"
            files = glob.glob(pattern)
            
            if files:
                filename = files[0]  # 첫 번째 매칭 파일 사용
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print(f"[INFO] 사건 결과 로드 완료: {filename}")
                return [data]
            else:
                print(f"[ERROR] 파일을 찾을 수 없습니다: {pattern}")
                return []
        else:
            # 모든 case_result_*.json 파일 로드
            pattern = "results/case_result_*.json"
            files = glob.glob(pattern)
            results = []
            
            for filepath in files:
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    results.append(data)
                    print(f"[INFO] 사건 결과 로드 완료: {filepath}")
                except Exception as e:
                    print(f"[ERROR] 파일 로드 실패 {filepath}: {e}")
            
            return results
            
    except Exception as e:
        print(f"[ERROR] 데이터 로드 실패: {e}")
        return []

def connect_to_google_sheets():
    """구글 시트에 연결합니다."""
    try:
        # 서비스 계정 키 파일 경로
        credentials_file = "./api/certification/service-account.json"
        
        if not os.path.exists(credentials_file):
            print(f"[ERROR] 서비스 계정 키 파일을 찾을 수 없습니다: {credentials_file}")
            print("[INFO] 구글 클라우드 콘솔에서 서비스 계정 키를 다운로드하고 api/certification/ 폴더에 service-account.json으로 저장하세요")
            return None
        
        # 구글 시트 연결
        gc = gspread.service_account(filename=credentials_file)
        
        # 스프레드시트 ID (기존 설정과 동일)
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
        # 파일명에서 안전한 워크시트명 생성
        safe_name = case_number.replace('/', '_').replace('\\', '_').replace(':', '_')
        worksheet_name = f"진행내용_{safe_name}"
        
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

def save_progress_data(worksheet, result_data):
    """진행내용 데이터를 구글 시트에 저장합니다."""
    try:
        if not result_data or 'progressData' not in result_data:
            print("[ERROR] 유효한 진행내용 데이터가 없습니다")
            return False
        
        progress_data = result_data['progressData']
        if not progress_data:
            print("[WARNING] 진행내용 데이터가 비어있습니다")
            return False
        
        # 헤더 설정
        headers = ['일자', '내용', '결과', '공시문']
        worksheet.update('A1:D1', [headers])
        
        # 데이터 행들 저장
        data_rows = []
        for row in progress_data:
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
        case_info = result_data.get('caseData', {})
        worksheet.update(f'A{metadata_row}:D{metadata_row}', [
            ['사건번호', case_info.get('caseNumber', ''), '당사자명', case_info.get('partyName', '')]
        ])
        
        metadata_row += 1
        worksheet.update(f'A{metadata_row}:D{metadata_row}', [
            ['법원', case_info.get('courtName', ''), '캡차입력', result_data.get('captchaInput', '')]
        ])
        
        metadata_row += 1
        worksheet.update(f'A{metadata_row}:D{metadata_row}', [
            ['저장일시', result_data.get('extractedAt', ''), '브라우저ID', result_data.get('browserId', '')]
        ])
        
        print(f"[SUCCESS] 진행내용 데이터가 구글 시트에 저장되었습니다")
        return True
        
    except Exception as e:
        print(f"[ERROR] 데이터 저장 실패: {e}")
        return False

def main():
    """메인 함수"""
    print("=== Puppeteer 결과 → 구글 시트 연동기 ===")
    
    # 명령행 인수 처리
    if len(sys.argv) > 1:
        if sys.argv[1] == '--all':
            case_number = None
            print("[INFO] 모든 사건 결과를 처리합니다")
        else:
            case_number = sys.argv[1]
            print(f"[INFO] 처리할 사건번호: {case_number}")
    else:
        case_number = None
        print("[INFO] 모든 사건 결과를 처리합니다")
    
    # 1. Puppeteer 결과 데이터 로드
    results = load_puppeteer_result(case_number)
    if not results:
        print("[ERROR] 처리할 데이터가 없습니다")
        return
    
    # 2. 구글 시트 연결
    spreadsheet = connect_to_google_sheets()
    if not spreadsheet:
        print("[ERROR] 구글 시트에 연결할 수 없습니다")
        return
    
    # 3. 각 결과에 대해 워크시트 생성 및 데이터 저장
    success_count = 0
    for result in results:
        case_info = result.get('caseData', {})
        case_number = case_info.get('caseNumber', 'Unknown')
        
        print(f"\n[INFO] 사건 처리 중: {case_number}")
        
        # 워크시트 생성
        worksheet = create_progress_worksheet(spreadsheet, case_number)
        if not worksheet:
            print(f"[ERROR] 워크시트 생성 실패: {case_number}")
            continue
        
        # 데이터 저장
        if save_progress_data(worksheet, result):
            success_count += 1
            print(f"[SUCCESS] {case_number} 처리 완료")
        else:
            print(f"[ERROR] {case_number} 처리 실패")
    
    print(f"\n[SUCCESS] 처리 완료: {success_count}/{len(results)}개 사건")

if __name__ == "__main__":
    main()

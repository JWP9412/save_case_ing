#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
구글 시트 데이터 기반 워크시트 이름 생성
=====================================

역할: 구글 시트의 데이터를 읽어서 워크시트 이름을 생성
기능:
- 구글 시트에서 사건 데이터 읽기
- 피고 + 비고 + 법원 + 사건번호 조합으로 워크시트 이름 생성
- Puppeteer 결과를 해당 워크시트에 저장

사용법: python excel-based-sheets.py
"""

import gspread
import json
import os
import glob
from datetime import datetime

def load_google_sheet_data():
    """구글 시트에서 사건 데이터를 읽어옵니다."""
    try:
        # 구글 시트 연결
        gc = gspread.service_account(filename='./api/certification/service-account.json')
        
        # 기존 스프레드시트 열기 (ID로)
        spreadsheet_id = '1ShaDTz4pj8SRWvf3ahcVI-gStYK-dFSBPsS6BnDOFzU'
        spreadsheet = gc.open_by_key(spreadsheet_id)
        
        print(f"[INFO] 구글 시트 연결 성공: {spreadsheet.title}")
        
        # 모든 워크시트 목록 확인
        worksheets = spreadsheet.worksheets()
        print(f"[INFO] 워크시트 목록:")
        for i, ws in enumerate(worksheets):
            print(f"  {i+1}. {ws.title}")
        
        # 데이터가 있는 워크시트 찾기 ("사건 목록" 워크시트 사용)
        data_worksheet = None
        for ws in worksheets:
            if "사건 목록" in ws.title:
                data_worksheet = ws
                break
        
        if not data_worksheet and worksheets:
            data_worksheet = worksheets[0]
        
        if data_worksheet:
            print(f"[INFO] 데이터 워크시트 선택: {data_worksheet.title}")
            
            # 모든 데이터 읽기
            all_data = data_worksheet.get_all_records()
            print(f"[INFO] {len(all_data)}개 행의 데이터 로드 완료")
            
            return all_data, spreadsheet
        else:
            print("[ERROR] 워크시트를 찾을 수 없습니다")
            return None, None
            
    except Exception as e:
        print(f"[ERROR] 구글 시트 데이터 로드 실패: {e}")
        return None, None

def create_worksheet_name(row_data):
    """행 데이터로부터 워크시트 이름을 생성합니다."""
    try:
        # 컬럼명 매핑 (구글 시트의 실제 컬럼명에 맞게 조정)
        case_number = row_data.get('사건번호', '')
        defendant = row_data.get('피고', '')
        note = row_data.get('비고', '')
        court = row_data.get('법원', '')
        
        # 빈 값 처리
        if not case_number:
            case_number = 'Unknown'
        if not defendant:
            defendant = 'Unknown'
        if not note:
            note = 'Unknown'
        if not court:
            court = 'Unknown'
        
        # 워크시트 이름 생성 (안전한 문자로 변환)
        safe_name = f"{defendant}_{note}_{court}_{case_number}"
        safe_name = safe_name.replace('/', '_').replace('\\', '_').replace(':', '_')
        safe_name = safe_name.replace('*', '_').replace('?', '_').replace('[', '_').replace(']', '_')
        
        return safe_name
        
    except Exception as e:
        print(f"[ERROR] 워크시트 이름 생성 실패: {e}")
        return f"Unknown_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

def load_puppeteer_results():
    """Puppeteer 결과 파일들을 로드합니다."""
    try:
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

def find_matching_case(google_data, case_number):
    """구글 시트 데이터에서 해당 사건번호와 일치하는 행을 찾습니다."""
    try:
        for row in google_data:
            if row.get('사건번호', '') == case_number:
                return row
        return None
    except Exception as e:
        print(f"[ERROR] 사건 검색 실패: {e}")
        return None

def create_case_worksheet(spreadsheet, worksheet_name):
    """사건별 워크시트를 생성합니다."""
    try:
        # 워크시트 생성
        worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows=1000, cols=10)
        print(f"[INFO] 워크시트 생성: {worksheet_name}")
        return worksheet
        
    except Exception as e:
        print(f"[ERROR] 워크시트 생성 실패: {e}")
        return None

def save_case_data(worksheet, case_data, google_row_data):
    """사건 데이터를 워크시트에 저장합니다."""
    try:
        case_info = case_data.get('caseData', {})
        progress_data = case_data.get('progressData', [])
        
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
        
        # 메타데이터 추가 (구글 시트 데이터 포함)
        metadata_row = len(data_rows) + 3
        worksheet.update(f'A{metadata_row}:D{metadata_row}', [
            ['사건번호', case_info.get('caseNumber', ''), '당사자명', case_info.get('partyName', '')]
        ])
        
        metadata_row += 1
        worksheet.update(f'A{metadata_row}:D{metadata_row}', [
            ['법원', case_info.get('courtName', ''), '피고', google_row_data.get('피고', '')]
        ])
        
        metadata_row += 1
        worksheet.update(f'A{metadata_row}:D{metadata_row}', [
            ['비고', google_row_data.get('비고', ''), '캡차입력', case_data.get('captchaInput', '')]
        ])
        
        metadata_row += 1
        worksheet.update(f'A{metadata_row}:D{metadata_row}', [
            ['저장일시', case_data.get('extractedAt', ''), '브라우저ID', case_data.get('browserId', '')]
        ])
        
        print(f"[SUCCESS] 사건 데이터 저장 완료")
        return True
        
    except Exception as e:
        print(f"[ERROR] 데이터 저장 실패: {e}")
        return False

def main():
    """메인 함수"""
    print("=== 구글 시트 데이터 기반 워크시트 이름 생성 ===")
    
    # 1. 구글 시트에서 데이터 로드
    google_data, spreadsheet = load_google_sheet_data()
    if not google_data or not spreadsheet:
        print("[ERROR] 구글 시트 데이터를 로드할 수 없습니다")
        return
    
    # 2. Puppeteer 결과 로드
    results = load_puppeteer_results()
    if not results:
        print("[ERROR] 처리할 데이터가 없습니다")
        return
    
    # 3. 각 사건에 대해 워크시트 생성 및 데이터 저장
    success_count = 0
    for result in results:
        case_info = result.get('caseData', {})
        case_number = case_info.get('caseNumber', 'Unknown')
        
        print(f"\n[INFO] 사건 처리 중: {case_number}")
        
        # 구글 시트에서 해당 사건 데이터 찾기
        google_row_data = find_matching_case(google_data, case_number)
        if not google_row_data:
            print(f"[WARNING] 구글 시트에서 {case_number} 사건을 찾을 수 없습니다")
            # 기본 워크시트 이름 사용
            worksheet_name = f"진행내용_{case_number}"
        else:
            # 구글 시트 데이터로 워크시트 이름 생성
            worksheet_name = create_worksheet_name(google_row_data)
            print(f"[INFO] 워크시트 이름: {worksheet_name}")
        
        # 워크시트 생성
        worksheet = create_case_worksheet(spreadsheet, worksheet_name)
        if not worksheet:
            print(f"[ERROR] 워크시트 생성 실패: {case_number}")
            continue
        
        # 데이터 저장
        if save_case_data(worksheet, result, google_row_data or {}):
            success_count += 1
            print(f"[SUCCESS] {case_number} 처리 완료")
        else:
            print(f"[ERROR] {case_number} 처리 실패")
    
    print(f"\n[SUCCESS] 처리 완료: {success_count}/{len(results)}개 사건")

if __name__ == "__main__":
    main()

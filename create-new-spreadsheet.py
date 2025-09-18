#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
새로운 구글 스프레드시트 생성 및 Puppeteer 결과 저장
====================================================

역할: Puppeteer 결과를 위한 새로운 구글 스프레드시트 생성
기능:
- 새로운 구글 스프레드시트 생성
- 사건별 워크시트 생성
- 진행내용 데이터 저장

사용법: python create-new-spreadsheet.py
"""

import gspread
import json
import os
import glob
from datetime import datetime

def create_new_spreadsheet():
    """새로운 구글 스프레드시트를 생성합니다."""
    try:
        # 구글 시트 연결
        gc = gspread.service_account(filename='./api/certification/service-account.json')
        
        # 새로운 스프레드시트 생성
        spreadsheet_title = f"Puppeteer_진행내용_데이터_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        spreadsheet = gc.create(spreadsheet_title)
        
        print(f"[INFO] 새로운 스프레드시트 생성: {spreadsheet_title}")
        print(f"[INFO] 스프레드시트 ID: {spreadsheet.id}")
        print(f"[INFO] 스프레드시트 URL: https://docs.google.com/spreadsheets/d/{spreadsheet.id}")
        
        # 기본 워크시트 삭제 (새로 만들 예정)
        try:
            spreadsheet.del_worksheet(spreadsheet.sheet1)
        except:
            pass
        
        return spreadsheet
        
    except Exception as e:
        print(f"[ERROR] 스프레드시트 생성 실패: {e}")
        return None

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

def create_case_worksheet(spreadsheet, case_data):
    """사건별 워크시트를 생성합니다."""
    try:
        case_info = case_data.get('caseData', {})
        case_number = case_info.get('caseNumber', 'Unknown')
        party_name = case_info.get('partyName', 'Unknown')
        
        # 워크시트명 생성 (안전한 이름)
        safe_name = f"{case_number}_{party_name}".replace('/', '_').replace('\\', '_').replace(':', '_')
        worksheet_name = f"진행내용_{safe_name}"
        
        # 워크시트 생성
        worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows=1000, cols=10)
        print(f"[INFO] 워크시트 생성: {worksheet_name}")
        
        return worksheet
        
    except Exception as e:
        print(f"[ERROR] 워크시트 생성 실패: {e}")
        return None

def save_case_data(worksheet, case_data):
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
        
        # 메타데이터 추가
        metadata_row = len(data_rows) + 3
        worksheet.update(f'A{metadata_row}:D{metadata_row}', [
            ['사건번호', case_info.get('caseNumber', ''), '당사자명', case_info.get('partyName', '')]
        ])
        
        metadata_row += 1
        worksheet.update(f'A{metadata_row}:D{metadata_row}', [
            ['법원', case_info.get('courtName', ''), '캡차입력', case_data.get('captchaInput', '')]
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
    print("=== 새로운 구글 스프레드시트 생성 및 Puppeteer 결과 저장 ===")
    
    # 1. 새로운 스프레드시트 생성
    spreadsheet = create_new_spreadsheet()
    if not spreadsheet:
        print("[ERROR] 스프레드시트를 생성할 수 없습니다")
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
        
        # 워크시트 생성
        worksheet = create_case_worksheet(spreadsheet, result)
        if not worksheet:
            print(f"[ERROR] 워크시트 생성 실패: {case_number}")
            continue
        
        # 데이터 저장
        if save_case_data(worksheet, result):
            success_count += 1
            print(f"[SUCCESS] {case_number} 처리 완료")
        else:
            print(f"[ERROR] {case_number} 처리 실패")
    
    print(f"\n[SUCCESS] 처리 완료: {success_count}/{len(results)}개 사건")
    print(f"[INFO] 스프레드시트 URL: https://docs.google.com/spreadsheets/d/{spreadsheet.id}")

if __name__ == "__main__":
    main()


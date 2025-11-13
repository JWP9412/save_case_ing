#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
일괄 처리용 GUI 생성기
====================

역할: 여러 사건을 한번에 처리할 수 있는 GUI 생성
기능:
- 구글 시트에서 사건 목록 로드
- 사건 선택 (체크박스)
- 처리 옵션 설정
- 실시간 진행상황 모니터링
- 캡차 재시도 시스템

사용법: python batch_gui_maker.py
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import gspread
import json
import threading
import time
import subprocess
import os
import glob
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from gui_maker import CaptchaGUI
# from captcha_input import CaptchaInputHandler  # 필요시 사용
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 구글 시트 데이터 로드 함수 직접 구현
def load_google_sheet_data():
    """구글 시트에서 사건 데이터를 읽어옵니다."""
    try:
        import gspread
        # 구글 시트 연결
        gc = gspread.service_account(filename='./api/certification/service-account.json')
        
        # 기존 스프레드시트 열기 (ID로)
        spreadsheet_id = '1ShaDTz4pj8SRWvf3ahcVI-gStYK-dFSBPsS6BnDOFzU'
        spreadsheet = gc.open_by_key(spreadsheet_id)
        
        print(f"[INFO] 구글 시트 연결 성공: {spreadsheet.title}")
        
        # 모든 워크시트 목록 확인
        worksheets = spreadsheet.worksheets()
        
        # "사건 목록" 워크시트 찾기
        data_worksheet = None
        for ws in worksheets:
            if "사건 목록" in ws.title:
                data_worksheet = ws
                break
        
        if not data_worksheet and worksheets:
            data_worksheet = worksheets[0]
        
        if data_worksheet:
            print(f"[INFO] 데이터 워크시트 선택: {data_worksheet.title}")
            
            # 모든 데이터 읽기 (헤더 중복 문제 해결)
            try:
                all_data = data_worksheet.get_all_records()
            except Exception as header_error:
                print(f"[WARNING] 헤더 중복 오류: {header_error}")
                # 수동으로 헤더 설정하여 데이터 읽기
                all_values = data_worksheet.get_all_values()
                if len(all_values) > 1:
                    # 첫 번째 행을 헤더로 사용하고, 빈 컬럼명 처리
                    headers = all_values[0]
                    # 빈 헤더를 '비고'로 변경
                    for i, header in enumerate(headers):
                        if not header or header.strip() == '':
                            headers[i] = f'비고_{i}'
                    
                    # 데이터 행들 처리
                    data_rows = all_values[1:]
                    all_data = []
                    for row in data_rows:
                        if len(row) >= len(headers):  # 충분한 컬럼이 있는 경우만
                            row_dict = {}
                            for i, header in enumerate(headers):
                                if i < len(row):
                                    row_dict[header] = row[i]
                            all_data.append(row_dict)
                else:
                    all_data = []
            
            # 빈 행 필터링 (사건번호가 비어있는 행 제외)
            filtered_data = []
            for row in all_data:
                case_number = row.get('사건번호', '').strip()
                if case_number:  # 사건번호가 있는 경우만 추가
                    filtered_data.append(row)
            
            print(f"[INFO] {len(all_data)}개 행 중 {len(filtered_data)}개 유효한 데이터 로드 완료")
            
            return filtered_data, spreadsheet
        else:
            print("[ERROR] 워크시트를 찾을 수 없습니다")
            return None, None
            
    except Exception as e:
        print(f"[ERROR] 구글 시트 데이터 로드 실패: {e}")
        print(f"[ERROR] 오류 타입: {type(e).__name__}")
        import traceback
        print(f"[ERROR] 상세 오류: {traceback.format_exc()}")
        return None, None

class CaptchaInputDialog:
    """캡차 입력 다이얼로그"""
    def __init__(self, parent, case_number, image_path):
        self.parent = parent
        self.case_number = case_number
        self.image_path = image_path
        self.result = None
        self.dialog = None
        
    def show(self):
        """캡차 입력 다이얼로그 표시"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title(f"캡차 입력 - {self.case_number}")
        self.dialog.geometry("500x400")
        self.dialog.resizable(False, False)
        
        # 모달 다이얼로그로 설정
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # 중앙에 배치
        self.dialog.eval('tk::PlaceWindow . center')
        
        self.create_widgets()
        
        # 다이얼로그가 닫힐 때까지 대기
        self.dialog.wait_window()
        
        return self.result
    
    def create_widgets(self):
        """위젯 생성"""
        # 메인 프레임
        main_frame = tk.Frame(self.dialog, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 제목
        title_label = tk.Label(main_frame, text="자동입력방지문구 입력", 
                              font=("Arial", 14, "bold"), fg="blue")
        title_label.pack(pady=(0, 20))
        
        # 사건번호
        case_label = tk.Label(main_frame, text=f"사건번호: {self.case_number}", 
                             font=("Arial", 12), fg="red")
        case_label.pack(pady=(0, 10))
        
        # 캡차 이미지 영역
        image_frame = tk.Frame(main_frame, relief=tk.SUNKEN, bd=2, bg="white")
        image_frame.pack(fill=tk.X, pady=(0, 20))
        
        # 이미지 표시
        if self.image_path and os.path.exists(self.image_path):
            try:
                from PIL import Image, ImageTk
                img = Image.open(self.image_path)
                img = img.resize((300, 100), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                
                img_label = tk.Label(image_frame, image=photo, bg="white")
                img_label.image = photo  # 참조 유지
                img_label.pack(pady=10)
            except Exception as e:
                error_label = tk.Label(image_frame, text=f"이미지 로드 실패: {e}", 
                                     fg="red", bg="white")
                error_label.pack(pady=10)
        else:
            error_label = tk.Label(image_frame, text="캡차 이미지를 찾을 수 없습니다", 
                                 fg="red", bg="white")
            error_label.pack(pady=10)
        
        # 입력 안내
        instruction_label = tk.Label(main_frame, 
                                    text="위 이미지에서 6글자 자동입력방지문구를 입력하세요:",
                                    font=("Arial", 11))
        instruction_label.pack(pady=(0, 10))
        
        # 입력 필드
        self.captcha_var = tk.StringVar()
        self.captcha_entry = tk.Entry(main_frame, textvariable=self.captcha_var, 
                                    font=("Arial", 14), width=10, justify=tk.CENTER)
        self.captcha_entry.pack(pady=(0, 20))
        self.captcha_entry.focus()
        
        # 버튼 프레임
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        # 확인 버튼
        ok_btn = tk.Button(button_frame, text="확인", 
                          font=("Arial", 12), bg="lightgreen", width=10,
                          command=self.ok_clicked)
        ok_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 취소 버튼
        cancel_btn = tk.Button(button_frame, text="취소", 
                              font=("Arial", 12), bg="lightcoral", width=10,
                              command=self.cancel_clicked)
        cancel_btn.pack(side=tk.LEFT)
        
        # 엔터키로 확인
        self.captcha_entry.bind('<Return>', lambda e: self.ok_clicked())
        
    def ok_clicked(self):
        """확인 버튼 클릭"""
        captcha_text = self.captcha_var.get().strip()
        if len(captcha_text) == 6:
            self.result = captcha_text
            self.dialog.destroy()
        else:
            messagebox.showwarning("경고", "6글자를 정확히 입력해주세요.")
    
    def cancel_clicked(self):
        """취소 버튼 클릭"""
        self.result = None
        self.dialog.destroy()

class BatchProcessingGUI:
    def __init__(self):
        """일괄 처리 GUI 초기화"""
        self.root = None
        self.case_list = []
        self.selected_cases = []
        self.processing = False
        self.progress_var = None
        self.status_text = None
        self.case_checkboxes = {}
        self.processing_thread = None
        
        # 브라우저 WebSocket URL 저장 (사건번호: ws_url)
        self.browser_ws_urls = {}
        # 브라우저 프로세스 저장 (사건번호: process)
        self.browser_processes = {}
        
        # 설정 옵션 (root 생성 후 초기화)
        self.max_parallel = None
        self.max_retry = None
        self.retry_delay = None
        
    def create_window(self):
        """메인 윈도우 생성"""
        self.root = tk.Tk()
        self.root.title("사건 일괄 처리 시스템 v2.0")
        self.root.geometry("1400x800")
        self.root.resizable(True, True)
        
        # 배경색 설정 (현대적인 다크 테마)
        self.root.configure(bg="#2C3E50")
        
        # 중앙에 배치
        self.root.eval('tk::PlaceWindow . center')
        
        # Tkinter 변수 초기화 (root 생성 후)
        self.max_parallel = tk.IntVar(value=3)
        self.max_retry = tk.IntVar(value=3)
        self.retry_delay = tk.IntVar(value=2)
        
        return self.root
    
    def create_header(self, parent):
        """헤더 영역 생성"""
        header_frame = tk.Frame(parent, bg="#34495E", height=120)
        header_frame.pack(fill=tk.X, padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        # 제목
        title_label = tk.Label(header_frame, text="⚖️ 사건 일괄 처리 시스템", 
                              font=("맑은 고딕", 24, "bold"), bg="#34495E", fg="#ECF0F1")
        title_label.pack(pady=(20, 5))
        
        # 부제목 ("대법원" 제거)
        subtitle_label = tk.Label(header_frame, text="사건 조회 자동화 시스템 v2.0", 
                                 font=("맑은 고딕", 11), bg="#34495E", fg="#BDC3C7")
        subtitle_label.pack(pady=(0, 15))
        
        return header_frame
    
    def create_control_panel(self, parent):
        """제어 패널 생성"""
        control_frame = tk.LabelFrame(parent, text="🎛️ 제어 패널", 
                                     font=("맑은 고딕", 12, "bold"), 
                                     bg="#ECF0F1", fg="#2C3E50",
                                     relief=tk.RIDGE, bd=2)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 버튼 프레임
        button_frame = tk.Frame(control_frame, bg="#ECF0F1")
        button_frame.pack(fill=tk.X, padx=15, pady=15)
        
        # 구글 시트 로드 버튼
        load_btn = tk.Button(button_frame, text="📊 구글 시트 로드", 
                            font=("맑은 고딕", 10, "bold"), bg="#27AE60", fg="white", 
                            width=18, height=2, relief=tk.RAISED, bd=3,
                            activebackground="#229954", cursor="hand2",
                            command=self.load_google_sheet)
        load_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 전체 선택/해제 버튼
        select_all_btn = tk.Button(button_frame, text="✅ 전체 선택", 
                                  font=("맑은 고딕", 10, "bold"), bg="#3498DB", fg="white",
                                  width=18, height=2, relief=tk.RAISED, bd=3,
                                  activebackground="#2980B9", cursor="hand2",
                                  command=self.select_all_cases)
        select_all_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        deselect_all_btn = tk.Button(button_frame, text="❌ 전체 해제", 
                                    font=("맑은 고딕", 10, "bold"), bg="#95A5A6", fg="white",
                                    width=18, height=2, relief=tk.RAISED, bd=3,
                                    activebackground="#7F8C8D", cursor="hand2",
                                    command=self.deselect_all_cases)
        deselect_all_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 캡차 이미지 로드 버튼 (이름 변경)
        self.start_btn = tk.Button(button_frame, text="🖼️ 캡차 이미지 로드", 
                                  font=("맑은 고딕", 10, "bold"), bg="#E67E22", fg="white",
                                  width=18, height=2, relief=tk.RAISED, bd=3,
                                  activebackground="#D35400", cursor="hand2",
                                  command=self.start_batch_processing)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 캡차 입력 완료 버튼
        self.complete_btn = tk.Button(button_frame, text="✔️ 캡차 입력 완료", 
                                     font=("맑은 고딕", 10, "bold"), bg="#16A085", fg="white",
                                     width=18, height=2, relief=tk.RAISED, bd=3,
                                     activebackground="#138D75", cursor="hand2",
                                     command=self.start_processing_thread, state=tk.DISABLED)
        self.complete_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 중지 버튼
        self.stop_btn = tk.Button(button_frame, text="⛔ 처리 중지", 
                                 font=("맑은 고딕", 10, "bold"), bg="#E74C3C", fg="white",
                                 width=18, height=2, relief=tk.RAISED, bd=3,
                                 activebackground="#C0392B", cursor="hand2",
                                 command=self.stop_batch_processing, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT)
        
        return control_frame
    
    def create_settings_panel(self, parent):
        """설정 패널 생성"""
        settings_frame = tk.LabelFrame(parent, text="⚙️ 처리 설정", 
                                      font=("맑은 고딕", 12, "bold"),
                                      bg="#ECF0F1", fg="#2C3E50",
                                      relief=tk.RIDGE, bd=2)
        settings_frame.pack(fill=tk.X, padx=10, pady=5)
        
        settings_inner = tk.Frame(settings_frame, bg="#ECF0F1")
        settings_inner.pack(fill=tk.X, padx=15, pady=12)
        
        # 병렬 처리 수
        tk.Label(settings_inner, text="⚡ 병렬 처리 수:", 
                font=("맑은 고딕", 10, "bold"), bg="#ECF0F1").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        parallel_spin = tk.Spinbox(settings_inner, from_=1, to=10, textvariable=self.max_parallel, 
                                  width=8, font=("맑은 고딕", 10), relief=tk.SUNKEN, bd=2)
        parallel_spin.grid(row=0, column=1, sticky=tk.W, padx=(0, 30))
        
        # 캡차 재시도 횟수
        tk.Label(settings_inner, text="🔄 캡차 재시도 횟수:", 
                font=("맑은 고딕", 10, "bold"), bg="#ECF0F1").grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        retry_spin = tk.Spinbox(settings_inner, from_=1, to=10, textvariable=self.max_retry, 
                               width=8, font=("맑은 고딕", 10), relief=tk.SUNKEN, bd=2)
        retry_spin.grid(row=0, column=3, sticky=tk.W, padx=(0, 30))
        
        # 재시도 간 대기시간
        tk.Label(settings_inner, text="⏱️ 재시도 간 대기시간(초):", 
                font=("맑은 고딕", 10, "bold"), bg="#ECF0F1").grid(row=0, column=4, sticky=tk.W, padx=(0, 10))
        delay_spin = tk.Spinbox(settings_inner, from_=1, to=10, textvariable=self.retry_delay, 
                               width=8, font=("맑은 고딕", 10), relief=tk.SUNKEN, bd=2)
        delay_spin.grid(row=0, column=5, sticky=tk.W)
        
        return settings_frame
    
    def create_case_list_panel(self, parent):
        """사건 목록 패널 생성"""
        case_frame = tk.LabelFrame(parent, text="📋 사건 목록", 
                                  font=("맑은 고딕", 12, "bold"),
                                  bg="#ECF0F1", fg="#2C3E50",
                                  relief=tk.RIDGE, bd=2, padx=0, pady=0)
        case_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 메인 컨테이너 (헤더 + 데이터를 같은 공간에)
        main_container = tk.Frame(case_frame, bg="white", bd=0, padx=0, pady=0)
        main_container.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        # 고정 헤더
        self.header_container = tk.Frame(main_container, bg="#34495E", height=40, bd=0)
        self.header_container.pack(fill=tk.X, side=tk.TOP, padx=0, pady=0)
        self.header_container.pack_propagate(False)
        
        # 스크롤 영역 (Canvas) - 인스턴스 변수로 저장
        self.case_canvas = tk.Canvas(main_container, bg="white", highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=self.case_canvas.yview)
        self.case_list_frame = tk.Frame(self.case_canvas, bg="white", bd=0, padx=0, pady=0)
        
        self.case_list_frame.bind(
            "<Configure>",
            lambda e: self.case_canvas.configure(scrollregion=self.case_canvas.bbox("all"))
        )
        
        self.case_canvas.create_window((0, 0), window=self.case_list_frame, anchor="nw")
        self.case_canvas.configure(yscrollcommand=scrollbar.set)
        
        # 마우스 휠 스크롤
        def on_mousewheel(event):
            self.case_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        self.case_canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        self.case_canvas.pack(side="left", fill="both", expand=True, padx=0, pady=0)
        scrollbar.pack(side="right", fill="y", padx=0, pady=0)
        
        return case_frame
    
    def create_progress_panel(self, parent):
        """진행상황 패널 생성"""
        progress_frame = tk.LabelFrame(parent, text="📊 진행상황", 
                                      font=("맑은 고딕", 12, "bold"),
                                      bg="#ECF0F1", fg="#2C3E50",
                                      relief=tk.RIDGE, bd=2)
        progress_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 진행률 바
        self.progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100, 
                                      mode='determinate')
        progress_bar.pack(fill=tk.X, padx=15, pady=10)
        
        # 상태 텍스트 (로그 창 - 크게!)
        self.status_text = scrolledtext.ScrolledText(progress_frame, 
                                                     font=("맑은 고딕", 9),
                                                     bg="#34495E", fg="#ECF0F1",
                                                     relief=tk.SUNKEN, bd=2,
                                                     wrap=tk.WORD)
        self.status_text.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))
        
        return progress_frame
    
    def load_google_sheet(self):
        """구글 시트에서 사건 목록 로드"""
        try:
            self.log_message("구글 시트 연결 중...")
            google_data, spreadsheet = load_google_sheet_data()
            
            if not google_data:
                messagebox.showerror("오류", "구글 시트 데이터를 로드할 수 없습니다.")
                return
            
            self.case_list = google_data
            self.log_message(f"✅ {len(google_data)}개 사건 로드 완료")
            
            # 사건 목록 UI 업데이트
            self.update_case_list_ui()
            
        except Exception as e:
            self.log_message(f"❌ 구글 시트 로드 실패: {e}")
            messagebox.showerror("오류", f"구글 시트 로드 실패: {e}")
    
    def update_case_list_ui(self):
        """사건 목록 UI 업데이트"""
        try:
            self.log_message(f"🔄 [DEBUG] update_case_list_ui 시작 - 사건 수: {len(self.case_list)}")
            
            # 기존 위젯 제거
            for widget in self.case_list_frame.winfo_children():
                widget.destroy()
            for widget in self.header_container.winfo_children():
                widget.destroy()
            
            self.case_checkboxes = {}
            
            self.log_message(f"🔄 [DEBUG] 기존 위젯 제거 완료")
        except Exception as e:
            self.log_message(f"❌ [ERROR] update_case_list_ui 오류: {e}")
            import traceback
            self.log_message(f"❌ [ERROR] 스택 트레이스: {traceback.format_exc()}")
            return
        
        try:
            # 컬럼 고정 너비 (픽셀) - 전역 사용
            self.col_widths = [50, 120, 90, 140, 110, 180, 90, 90, 120]
            col_names = ["선택", "사건번호", "피고", "법원", "비고", "캡차 이미지", "캡차 입력", "상태", "최근 업데이트"]
            
            self.log_message(f"🔄 [DEBUG] 헤더 생성 시작")
            
            # 고정 헤더 생성 (pack 사용)
            header_frame = tk.Frame(self.header_container, bg="#34495E")
            header_frame.pack(fill=tk.BOTH, expand=True)
            
            for col_idx, (name, width) in enumerate(zip(col_names, self.col_widths)):
                header_cell = tk.Frame(header_frame, bg="#34495E", width=width, height=40)
                header_cell.pack(side=tk.LEFT)
                header_cell.pack_propagate(False)
                
                label = tk.Label(header_cell, text=name, 
                               font=("맑은 고딕", 10, "bold"), 
                               bg="#34495E", fg="white",
                               anchor=tk.CENTER)
                label.pack(fill=tk.BOTH, expand=True)
            
            self.log_message(f"✅ [DEBUG] 헤더 생성 완료")
        except Exception as e:
            self.log_message(f"❌ [ERROR] 헤더 생성 오류: {e}")
            import traceback
            self.log_message(f"❌ [ERROR] 스택 트레이스: {traceback.format_exc()}")
            return
        
        # 사건 목록
        self.case_inputs = {}  # 캡차 입력 필드 저장
        self.case_status = {}  # 상태 라벨 저장
        self.case_images = {}  # 캡차 이미지 라벨 저장
        self.case_frames = {}  # 사건 프레임 저장 (하이라이트용)
        self.case_start_times = {}  # 각 사건 처리 시작 시간
        self.case_update_labels = {}  # 업데이트 D+n 라벨 저장
        self.case_update_date_labels = {}  # 업데이트 날짜 라벨 저장
        
        self.log_message(f"🔄 [DEBUG] 사건 목록 생성 시작 - {len(self.case_list)}개")
        
        # 전체 너비 계산 (모든 칼럼 너비의 합)
        total_width = sum(self.col_widths)
        
        for i, case in enumerate(self.case_list):
            if i == 0:
                self.log_message(f"🔄 [DEBUG] 첫 번째 사건 생성 중: {case.get('사건번호', '')}")
            # 번갈아가는 배경색 (현대적인 색상)
            bg_color = "#FFFFFF" if i % 2 == 0 else "#F8F9FA"
            
            # 사건 행 컨테이너 (case_frame + 가로 구분선)
            row_container = tk.Frame(self.case_list_frame, bg="white", bd=0, padx=0, pady=0)
            row_container.pack(fill=tk.X, pady=0, padx=0)
            
            case_frame = tk.Frame(row_container, bg=bg_color, height=60, width=total_width, bd=0)
            case_frame.pack(fill=tk.X, padx=0, pady=0)
            case_frame.pack_propagate(False)
            
            # 첫 번째 row의 위치 디버깅
            if i == 0:
                row_container.update_idletasks()
                row_y = row_container.winfo_y()
                self.log_message(f"🔍 [DEBUG] 첫 번째 row_container Y 위치: {row_y}")
            
            # 가로 구분선
            separator = tk.Frame(row_container, bg="#DEE2E6", height=1, width=total_width)
            separator.pack(fill=tk.X)
            
            # 체크박스 (0번 칼럼)
            var = tk.BooleanVar()
            checkbox_frame = tk.Frame(case_frame, bg=bg_color, width=self.col_widths[0], height=60)
            checkbox_frame.pack(side=tk.LEFT)
            checkbox_frame.pack_propagate(False)
            checkbox = tk.Checkbutton(checkbox_frame, variable=var, bg=bg_color,
                                     command=lambda idx=i: self.on_checkbox_change(idx))
            checkbox.pack(anchor=tk.CENTER, expand=True)
            
            # 사건 정보 (고정 너비로 정렬)
            case_number = case.get('사건번호', '')
            defendant = case.get('피고', '')
            court = case.get('법원', '')
            note = case.get('비고', '')
            
            # 최근 업데이트 날짜 및 경과 일수 조회
            history = self.load_update_history()
            case_data = history.get(case_number, {})
            
            # 구버전 호환성
            if isinstance(case_data, str):
                last_update_date = case_data
            else:
                last_update_date = case_data.get('last_update', '')
            
            days_since = self.get_days_since_update(case)
            
            # 사건번호, 피고, 법원, 비고 (1-4번 칼럼)
            info_texts = [case_number, defendant, court, note]
            
            if i == 0:
                self.log_message(f"🔍 [DEBUG] 첫 번째 사건 데이터: {info_texts}")
            
            for col_idx, text in enumerate(info_texts, start=1):
                info_frame = tk.Frame(case_frame, bg=bg_color, width=self.col_widths[col_idx], height=60)
                info_frame.pack(side=tk.LEFT)
                info_frame.pack_propagate(False)
                
                label = tk.Label(info_frame, text=text, 
                               font=("맑은 고딕", 10, "bold"),  # 크기 증가 + 볼드
                               bg=bg_color, fg="black",  # 명확한 검정색
                               anchor=tk.W, padx=5, pady=5)
                label.pack(fill=tk.BOTH, expand=True)
                
                if i == 0 and col_idx == 1:
                    self.log_message(f"🔍 [DEBUG] Label 생성: text='{text}', fg='black', bg='{bg_color}'")
                    # Label 크기 확인 (update_idletasks 후)
                    label.update_idletasks()
                    label_width = label.winfo_width()
                    label_height = label.winfo_height()
                    self.log_message(f"🔍 [DEBUG] Label 실제 크기: {label_width}x{label_height}")
                    self.log_message(f"🔍 [DEBUG] info_frame 크기: {info_frame.winfo_width()}x{info_frame.winfo_height()}")
            
            # 캡차 이미지 프레임 (5번 칼럼)
            image_frame = tk.Frame(case_frame, bg=bg_color, width=self.col_widths[5], height=60)
            image_frame.pack(side=tk.LEFT)
            image_frame.pack_propagate(False)
            
            image_label = tk.Label(image_frame, text="대기중", 
                                 font=("맑은 고딕", 10, "bold"), fg="black", 
                                 bg="#E9ECEF", anchor=tk.CENTER,
                                 relief=tk.SOLID, bd=1)
            image_label.pack(fill=tk.BOTH, expand=True, padx=2, pady=5)
            
            # 캡차 입력 프레임 (6번 칼럼)
            captcha_frame = tk.Frame(case_frame, bg=bg_color, width=self.col_widths[6], height=60)
            captcha_frame.pack(side=tk.LEFT)
            captcha_frame.pack_propagate(False)
            
            captcha_var = tk.StringVar()
            captcha_entry = tk.Entry(captcha_frame, textvariable=captcha_var, 
                                   font=("Arial", 10, "bold"), justify=tk.CENTER, 
                                   bg="white", fg="black", 
                                   relief=tk.SOLID, bd=1)
            captcha_entry.pack(fill=tk.BOTH, expand=True, padx=2, pady=5)
            
            # 6글자 숫자만 입력 가능하도록 제한
            def validate_captcha_input(char):
                current_text = captcha_var.get()
                return char.isdigit() and len(current_text) < 6
            
            captcha_entry.config(validate='key', validatecommand=(captcha_entry.register(validate_captcha_input), '%S'))
            
            # 엔터키 이벤트 바인딩
            captcha_entry.bind('<Return>', lambda event, idx=i: self.on_captcha_enter(idx))
            
            # 상태 프레임 (7번 칼럼)
            status_frame = tk.Frame(case_frame, bg=bg_color, width=self.col_widths[7], height=60)
            status_frame.pack(side=tk.LEFT)
            status_frame.pack_propagate(False)
            
            status_label = tk.Label(status_frame, text="⏸️ 대기", 
                                  font=("맑은 고딕", 10, "bold"), fg="black",
                                  bg=bg_color, anchor=tk.CENTER, pady=5)
            status_label.pack(fill=tk.BOTH, expand=True)
            
            # 최근 업데이트 프레임 (8번 칼럼 - 날짜 + D+n)
            update_frame = tk.Frame(case_frame, bg=bg_color, width=self.col_widths[8], height=60)
            update_frame.pack(side=tk.LEFT)
            update_frame.pack_propagate(False)
            
            update_container = tk.Frame(update_frame, bg=bg_color)
            update_container.pack(fill=tk.BOTH, expand=True)
            
            # 날짜 표시 (위)
            date_label = None
            if last_update_date:
                date_str = last_update_date.split(' ')[0]  # 날짜만 추출
                date_label = tk.Label(update_container, text=date_str, 
                                    font=("맑은 고딕", 8, "bold"), fg="black",
                                    bg=bg_color, anchor=tk.CENTER)
                date_label.pack(pady=(5,0))
            
            # D+n 표시 (아래)
            update_label = tk.Label(update_container, text=days_since, 
                                  font=("맑은 고딕", 11, "bold"), 
                                  fg="blue" if days_since != "-" else "black",
                                  bg=bg_color, anchor=tk.CENTER)
            update_label.pack(pady=(0,5))
            
            # 저장
            self.case_checkboxes[i] = var
            self.case_inputs[i] = captcha_var
            self.case_status[i] = status_label
            self.case_images[i] = image_label
            self.case_frames[i] = case_frame  # 프레임 저장 (하이라이트용)
            self.case_update_labels[i] = update_label  # D+n 라벨 저장
            self.case_update_date_labels[i] = date_label  # 날짜 라벨 저장
            
            if i == 0:
                self.log_message(f"✅ [DEBUG] 첫 번째 사건 생성 완료")
            
            self.log_message(f"✅ [DEBUG] 사건 {i+1}/{len(self.case_list)} 생성 완료: {case_number}")
        
        self.log_message(f"✅ [DEBUG] 전체 사건 목록 생성 완료")
        
        # 강제로 UI 업데이트
        try:
            self.case_list_frame.update_idletasks()
            self.header_container.update_idletasks()
            
            # 디버그: 프레임 크기 확인
            frame_width = self.case_list_frame.winfo_width()
            frame_height = self.case_list_frame.winfo_height()
            frame_children = len(self.case_list_frame.winfo_children())
            self.log_message(f"🔍 [DEBUG] case_list_frame 크기: {frame_width}x{frame_height}, 자식: {frame_children}")
            
            # Canvas scrollregion 명시적 업데이트 - (0, 0)에서 시작하도록 강제
            if hasattr(self, 'case_canvas'):
                self.case_list_frame.update_idletasks()
                frame_w = self.case_list_frame.winfo_width()
                frame_h = self.case_list_frame.winfo_height()
                
                # Canvas window의 실제 위치 확인
                window_id = self.case_canvas.find_all()[0] if self.case_canvas.find_all() else None
                if window_id:
                    window_coords = self.case_canvas.coords(window_id)
                    self.log_message(f"🔍 [DEBUG] Canvas window 좌표: {window_coords}")
                
                self.case_canvas.configure(scrollregion=(0, 0, frame_w, frame_h))
                # 스크롤을 맨 위로 이동
                self.case_canvas.yview_moveto(0)
                self.log_message(f"✅ [DEBUG] Canvas scrollregion 업데이트: (0, 0, {frame_w}, {frame_h})")
                
                # Canvas 크기 확인
                canvas_width = self.case_canvas.winfo_width()
                canvas_height = self.case_canvas.winfo_height()
                self.log_message(f"🔍 [DEBUG] Canvas 크기: {canvas_width}x{canvas_height}")
            
            self.root.update_idletasks()
            self.log_message(f"✅ [DEBUG] UI 강제 업데이트 완료")
        except Exception as e:
            self.log_message(f"⚠️ [DEBUG] UI 업데이트 오류: {e}")
            import traceback
            self.log_message(f"⚠️ [DEBUG] 스택 트레이스: {traceback.format_exc()}")
    
    def select_all_cases(self):
        """전체 사건 선택"""
        for var in self.case_checkboxes.values():
            var.set(True)
        self.log_message("✅ 전체 사건 선택 완료")
    
    def deselect_all_cases(self):
        """전체 사건 해제"""
        for var in self.case_checkboxes.values():
            var.set(False)
        self.log_message("✅ 전체 사건 해제 완료")
    
    def get_selected_cases(self):
        """선택된 사건 목록 반환 (인덱스 포함)"""
        selected = []
        print(f"[DEBUG] 체크박스 개수: {len(self.case_checkboxes)}")
        print(f"[DEBUG] 사건 목록 개수: {len(self.case_list)}")
        
        for i, var in self.case_checkboxes.items():
            is_checked = var.get()
            print(f"[DEBUG] 사건 {i}: {self.case_list[i].get('사건번호', '')} - 체크됨: {is_checked}")
            if is_checked:
                # (원래 인덱스, 사건 데이터) 튜플로 반환
                selected.append((i, self.case_list[i]))
        
        print(f"[DEBUG] 선택된 사건 수: {len(selected)}")
        return selected
    
    def on_checkbox_change(self, index):
        """체크박스 변경 이벤트 핸들러"""
        is_checked = self.case_checkboxes[index].get()
        case_number = self.case_list[index].get('사건번호', '')
        print(f"[DEBUG] 체크박스 변경: {case_number} - 체크됨: {is_checked}")
    
    def start_batch_processing(self):
        """캡차 이미지 로드 시작"""
        print("[DEBUG] 캡차 이미지 로드 버튼 클릭됨")
        selected_cases_with_index = self.get_selected_cases()
        selected_cases = [case for _, case in selected_cases_with_index]  # 데이터만 추출
        
        if not selected_cases:
            print("[DEBUG] 선택된 사건이 없음 - 경고 표시")
            messagebox.showwarning("경고", "처리할 사건을 선택해주세요.")
            return
        
        if self.processing:
            print("[DEBUG] 이미 처리 중 - 경고 표시")
            messagebox.showwarning("경고", "이미 처리 중입니다.")
            return
        
        print(f"[DEBUG] {len(selected_cases)}개 사건 선택됨 - 캡차 이미지 로드 시작")
        
        # 직접 병렬 처리 실행 (캡차는 실제 처리 시에만 캡처)
        self.processing = True
        self.start_btn.config(text="🔄 로딩 중...", state=tk.DISABLED, bg="#95A5A6")
        self.stop_btn.config(state=tk.NORMAL)
        
        # 처리 스레드 시작
        self.processing_thread = threading.Thread(target=self.execute_actual_processing, args=(selected_cases,))
        self.processing_thread.daemon = True
        self.processing_thread.start()
    
    def stop_batch_processing(self):
        """일괄 처리 중지"""
        self.processing = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.log_message("⏹️ 처리 중지됨")
    
    
    def execute_actual_processing(self, cases):
        """실제 처리 실행 (병렬 처리)"""
        if not cases:
            return
        
        self.log_message("🔄 병렬 처리 시작")
        
        # 병렬 처리 (ThreadPoolExecutor 사용)
        max_workers = min(self.max_parallel.get(), len(cases))
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 각 사건에 대해 병렬 처리 시작
            future_to_case = {}
            for case in cases:
                if not self.processing:
                    break
                
                case_number = case.get('사건번호', '')
                case_index = self.find_case_index(case_number)
                
                future = executor.submit(self.process_single_case_parallel, case, case_index)
                future_to_case[future] = (case_number, case_index)
            
            # 결과 수집
            for future in as_completed(future_to_case):
                if not self.processing:
                    break
                
                case_number, case_index = future_to_case[future]
                try:
                    success = future.result()
                    if success:
                        self.log_message(f"✅ 처리 완료: {case_number}")
                    else:
                        self.log_message(f"❌ 처리 실패: {case_number}")
                except Exception as e:
                    self.log_message(f"❌ 처리 오류: {case_number} - {e}")
        
        self.log_message("🎉 모든 캡차 이미지 로드 완료!")
        self.processing = False
        # 버튼 상태 변경 (Thread-Safe)
        self.root.after(0, lambda: self.start_btn.config(text="🖼️ 캡차 이미지 로드", state=tk.NORMAL, bg="#E67E22"))
        self.root.after(0, lambda: self.stop_btn.config(state=tk.DISABLED))
    
    def process_single_case_parallel(self, case, case_index):
        """병렬 처리용 단일 사건 처리 (캡차는 실제 처리 시에만 캡처)"""
        case_number = case.get('사건번호', '')
        
        try:
            # 처리 시작 시간 기록
            import time
            self.case_start_times[case_index] = time.time()
            
            # 상태 업데이트 (이모지 + 애니메이션)
            self.update_case_status(case_index, "처리중", "orange", "🔄")
            
            # 실제 처리 실행 (Puppeteer에서 캡차 캡처 및 처리)
            result_data = self.execute_case_processing_with_captcha(case, case_index)
            
            # 처리 시간 계산
            elapsed_time = int(time.time() - self.case_start_times[case_index])
            
            if result_data:
                # 캡차 이미지 로드만 완료된 상태 (실제 크롤링은 "캡차 입력 완료" 버튼 클릭 후 실행)
                self.update_case_status(case_index, "입력대기", "blue", "⏳")
                self.log_message(f"✅ 캡차 이미지 로드 완료: {case_number} (소요 시간: {elapsed_time}초)")
                return True
            else:
                self.update_case_status(case_index, f"실패 ({elapsed_time}초)", "red", "❌")
                return False
                
        except Exception as e:
            elapsed_time = int(time.time() - self.case_start_times.get(case_index, time.time()))
            self.log_message(f"❌ 처리 오류: {case_number} - {e}")
            self.update_case_status(case_index, f"오류 ({elapsed_time}초)", "red", "⚠️")
            return False
    
    def get_captcha_input(self, case_index):
        """캡차 입력값 가져오기"""
        if case_index in self.case_inputs:
            return self.case_inputs[case_index].get()
        return None
    
    def on_captcha_enter(self, case_index):
        """캡차 입력 후 엔터키 처리 (다음 입력칸으로만 이동)"""
        captcha_input = self.get_captcha_input(case_index)
        if captcha_input and captcha_input.strip():
            # 입력 길이 검증
            if len(captcha_input) == 6 and captcha_input.isdigit():
                self.log_message(f"✅ 캡차 입력 저장: {captcha_input} (사건 인덱스: {case_index}) - 길이: {len(captcha_input)}")
                # 상태를 "입력완료"로 변경 (실제 처리는 하지 않음)
                self.update_case_status(case_index, "입력완료", "blue")

                # 다음 입력칸으로 포커스 이동
                self.move_to_next_input(case_index)
            else:
                self.log_message(f"⚠️ 캡차 입력 형식 오류: {captcha_input} (길이: {len(captcha_input)}, 숫자여부: {captcha_input.isdigit()})")
        else:
            self.log_message(f"⚠️ 캡차 입력이 비어있습니다 (사건 인덱스: {case_index})")
    
    def move_to_next_input(self, current_case_index):
        """다음 입력칸으로 포커스 이동"""
        try:
            # 선택된 사건들 중에서 다음 사건 찾기
            selected_cases = self.get_selected_cases()
            next_index = None

            # 현재 사건 다음에 선택된 사건 찾기 (순서대로)
            for i in range(current_case_index + 1, len(selected_cases)):
                if i in self.case_inputs:  # 입력칸이 있는 경우
                    next_index = i
                    break

            # 다음 사건이 없으면 첫 번째 선택된 사건으로
            if next_index is None:
                for i in range(len(selected_cases)):
                    if i in self.case_inputs:
                        next_index = i
                        break

            if next_index is not None and next_index in self.case_inputs:
                # 다음 입력칸으로 포커스 이동 (Entry 위젯에 직접 접근)
                entry_widget = None
                for child in self.case_list_frame.winfo_children():
                    if isinstance(child, tk.Frame):
                        for grandchild in child.winfo_children():
                            if isinstance(grandchild, tk.Entry) and grandchild.grid_info().get('row') == 0 and grandchild.grid_info().get('column') == 6:
                                entry_widget = grandchild
                                break
                        if entry_widget:
                            break
                
                if entry_widget:
                    entry_widget.focus()
                    self.log_message(f"🔄 다음 입력칸으로 이동: 사건 인덱스 {next_index}")
                else:
                    self.log_message("⚠️ 입력칸을 찾을 수 없습니다")
            else:
                self.log_message("ℹ️ 다음 입력할 사건이 없습니다")

        except Exception as e:
            self.log_message(f"⚠️ 다음 입력칸 이동 실패: {e}")
    
    def start_processing_thread(self):
        """별도 스레드에서 캡차 입력 처리를 시작 (GUI 멈춤 방지)"""
        processing_thread = threading.Thread(target=self.process_all_captcha_inputs, daemon=True)
        processing_thread.start()
        self.log_message("🚀 백그라운드 처리 시작 - GUI는 계속 응답합니다!")
    
    def process_all_captcha_inputs(self):
        """모든 캡차 입력을 한번에 처리"""
        try:
            import time
            total_start_time = time.time()
            
            # 처리 플래그 설정 (중요!)
            self.processing = True
            
            self.log_message("🔄 모든 캡차 입력 처리 시작")
            
            # 완료 버튼 비활성화 (Thread-Safe)
            self.root.after(0, lambda: self.complete_btn.config(state=tk.DISABLED))
            self.root.after(0, lambda: self.start_btn.config(state=tk.DISABLED))
            self.root.after(0, lambda: self.stop_btn.config(state=tk.NORMAL))
            
            # 선택된 사건들 가져오기
            selected_cases = self.get_selected_cases()
            total_cases = len(selected_cases)
            
            # 진행률 초기화
            self.update_progress(0, f"⏳ 처리 준비 중... (0/{total_cases})")
            
            # 각 사건별로 처리
            completed = 0
            failed = 0
            
            self.log_message(f"🔄 [DEBUG] 처리할 사건 목록: {len(selected_cases)}개")
            for idx, (original_index, case) in enumerate(selected_cases):
                # 중지 플래그 확인
                if not self.processing:
                    self.log_message(f"⏹️ 사용자가 처리를 중지했습니다")
                    break
                
                self.log_message(f"🔄 [DEBUG] 루프 시작: {idx+1}/{len(selected_cases)} - 인덱스={original_index}")
                case_number = case.get('사건번호', '')
                
                # [DEBUG] 인덱스 확인
                self.log_message(f"📋 [DEBUG] 처리 중: original_index={original_index}, 사건번호={case_number}")
                self.log_message(f"📋 [DEBUG] case_inputs 키: {list(self.case_inputs.keys())}")
                self.log_message(f"📋 [DEBUG] original_index in case_inputs: {original_index in self.case_inputs}")
                
                if original_index in self.case_inputs:
                    captcha_input = self.get_captcha_input(original_index)
                    self.log_message(f"📋 [DEBUG] 캡차 입력값: '{captcha_input}'")
                    
                    # 처리 시작 시간
                    case_start_time = time.time()
                    self.case_start_times[original_index] = case_start_time
                    
                    # 진행률 업데이트 (예상 시간 포함)
                    current_progress = len([idx for idx, _ in selected_cases[:selected_cases.index((original_index, case)) + 1]])
                    progress_percent = (current_progress / total_cases) * 100
                    elapsed = int(time.time() - total_start_time)
                    if current_progress > 0:
                        avg_time = elapsed / current_progress
                        remaining_time = int(avg_time * (total_cases - current_progress))
                        self.update_progress(progress_percent, 
                            f"🔄 처리 중... ({current_progress}/{total_cases}) - {case_number} | 예상 남은 시간: {remaining_time}초")
                    else:
                        self.update_progress(progress_percent, f"🔄 처리 중... ({current_progress}/{total_cases}) - {case_number}")
                    
                    if captcha_input and captcha_input.strip():
                        self.log_message(f"📋 [DEBUG] GUI에서 가져온 캡차 입력: '{captcha_input}' (타입: {type(captcha_input).__name__}, 길이: {len(captcha_input)})")
                        # 입력 형식 검증
                        if len(captcha_input) == 6 and captcha_input.isdigit():
                            self.log_message(f"✅ [DEBUG] 캡차 형식 검증 통과: {captcha_input}")
                            self.log_message(f"🔄 처리 시작: {case_number} (캡차: {captcha_input})")
                            self.update_case_status(original_index, "처리중", "orange", "🔄")
                            
                            # 실제 Puppeteer 처리 실행
                            self.log_message(f"🔄 [DEBUG] execute_case_processing 호출 전")
                            result_data = self.execute_case_processing(case, captcha_input.strip())
                            self.log_message(f"🔄 [DEBUG] execute_case_processing 호출 후 - result_data 타입: {type(result_data)}")
                            
                            # 처리 시간 계산
                            elapsed_time = int(time.time() - case_start_time)
                            
                            try:
                                if result_data:
                                    self.log_message(f"🔄 [DEBUG] update_case_status 호출 전")
                                    self.update_case_status(original_index, f"완료 ({elapsed_time}초)", "green", "✅")
                                    self.log_message(f"🔄 [DEBUG] save_to_google_sheets 호출 전")
                                    row_count = self.save_to_google_sheets(case, result_data)
                                    self.log_message(f"🔄 [DEBUG] save_to_google_sheets 호출 후 - 행 개수: {row_count}")
                                    
                                    # 업데이트 타임스탬프 기록 및 GUI 갱신 (행 개수 포함)
                                    self.update_case_timestamp(case, original_index, row_count if row_count else 0)
                                    
                                    self.log_message(f"✅ 처리 완료: {case_number} (소요 시간: {elapsed_time}초)")
                                    completed += 1
                                else:
                                    self.update_case_status(original_index, f"실패 ({elapsed_time}초)", "red", "❌")
                                    self.log_message(f"❌ 처리 실패: {case_number}")
                                    failed += 1
                                
                                self.log_message(f"🔄 [DEBUG] 사건 처리 완료 블록 끝")
                            except Exception as e:
                                self.log_message(f"❌ [DEBUG] 사건 처리 중 예외 발생: {e}")
                                self.log_message(f"❌ [DEBUG] 예외 타입: {type(e).__name__}")
                                import traceback
                                self.log_message(f"❌ [DEBUG] 예외 스택: {traceback.format_exc()}")
                                self.update_case_status(original_index, f"오류 ({elapsed_time}초)", "red", "⚠️")
                                failed += 1
                        else:
                            self.log_message(f"⚠️ 캡차 입력 형식 오류: {case_number} (입력: {captcha_input}, 길이: {len(captcha_input)})")
                            self.update_case_status(original_index, "형식오류", "red", "⚠️")
                            failed += 1
                    else:
                        self.log_message(f"⚠️ 캡차 입력이 비어있음: {case_number}")
                        self.update_case_status(original_index, "입력없음", "red", "⚠️")
                        failed += 1
                
                self.log_message(f"🔄 [DEBUG] 루프 끝: {idx+1}/{len(selected_cases)} - 인덱스={original_index}")
            
            self.log_message(f"🔄 [DEBUG] 모든 사건 처리 완료 - 성공: {completed}, 실패: {failed}")
            
            # 모든 브라우저 프로세스 종료 (Node.js 프로세스만 종료하면 됨 - index.js가 browser.close() 호출)
            self.log_message(f"🔄 [DEBUG] 브라우저 프로세스 종료 시작")
            
            # Node.js 프로세스 종료
            for case_number, process in list(self.browser_processes.items()):
                try:
                    if process.poll() is None:
                        self.log_message(f"🔄 [DEBUG] Node.js 프로세스 종료: {case_number}")
                        process.kill()
                        try:
                            process.wait(timeout=2)
                        except:
                            pass
                        self.log_message(f"✅ 프로세스 종료 완료: {case_number}")
                except Exception as e:
                    self.log_message(f"⚠️ 프로세스 종료 실패: {case_number} - {e}")
            
            # 마지막으로 Chrome 프로세스 강제 종료 (혹시 남아있을 경우)
            try:
                import subprocess as sp
                import psutil
                self.log_message(f"🔄 [DEBUG] Chrome 프로세스 정리 중...")
                
                # psutil로 Chrome 프로세스 찾아서 종료
                chrome_killed = 0
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        # Chrome 프로세스이고 --remote-debugging-port가 있으면
                        if proc.info['name'] and 'chrome.exe' in proc.info['name'].lower():
                            cmdline = proc.info.get('cmdline', [])
                            if cmdline and any('--remote-debugging-port' in str(arg) for arg in cmdline):
                                self.log_message(f"🔄 [DEBUG] Chrome 프로세스 종료: PID {proc.info['pid']}")
                                proc.kill()  # 강제 종료
                                chrome_killed += 1
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        pass
                
                if chrome_killed > 0:
                    self.log_message(f"✅ Chrome 프로세스 {chrome_killed}개 종료 완료")
                else:
                    self.log_message(f"ℹ️ 종료할 Chrome 프로세스 없음")
                    
            except Exception as e:
                self.log_message(f"⚠️ Chrome 프로세스 정리 오류: {e}")
                # 최후의 수단: taskkill 사용
                try:
                    sp.run(['taskkill', '/F', '/IM', 'chrome.exe'], 
                          capture_output=True, timeout=3)
                    self.log_message(f"⚠️ taskkill로 Chrome 강제 종료 시도")
                except:
                    pass
            
            self.browser_processes.clear()
            self.browser_ws_urls.clear()
            self.log_message(f"✅ 모든 브라우저 프로세스 종료 완료")
            
            # 총 처리 시간
            total_elapsed = int(time.time() - total_start_time)
            
            # 최종 진행률 업데이트
            self.update_progress(100, f"✅ 처리 완료! (성공: {completed}, 실패: {failed}) | 총 소요 시간: {total_elapsed}초")
            self.log_message(f"🎉 모든 캡차 입력 처리 완료! (총 소요 시간: {total_elapsed}초)")
            
            # 완료 알림 MessageBox (Thread-Safe)
            self.root.after(0, lambda: messagebox.showinfo("처리 완료", 
                f"🎉 처리가 완료되었습니다!\n\n"
                f"✅ 성공: {completed}개\n"
                f"❌ 실패: {failed}개\n"
                f"📊 총 사건: {total_cases}개\n"
                f"⏱️ 총 소요 시간: {total_elapsed}초"))
            
            # 버튼 상태 복원 (Thread-Safe)
            self.root.after(0, lambda: self.complete_btn.config(state=tk.DISABLED))
            self.root.after(0, lambda: self.start_btn.config(text="🖼️ 캡차 이미지 로드", state=tk.NORMAL, bg="#E67E22"))
            self.root.after(0, lambda: self.stop_btn.config(state=tk.DISABLED))
            
        except Exception as e:
            self.log_message(f"❌ 캡차 입력 처리 오류: {e}")
            self.update_progress(0, "오류 발생")
            # 버튼 상태 복원 (Thread-Safe)
            self.root.after(0, lambda: self.complete_btn.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.start_btn.config(text="🖼️ 캡차 이미지 로드", state=tk.NORMAL, bg="#E67E22"))
            self.root.after(0, lambda: self.stop_btn.config(state=tk.DISABLED))

    def process_after_captcha_input(self, case_index, captcha_input):
        """캡차 입력 후 실제 처리 (사용하지 않음)"""
        pass
    
    def wait_for_captcha_input(self, case_index, timeout_seconds=300):
        """캡차 입력 대기 (최대 timeout_seconds초)"""
        import time
        start_time = time.time()
        
        while time.time() - start_time < timeout_seconds:
            if not self.processing:
                return None
                
            captcha_input = self.get_captcha_input(case_index)
            if captcha_input and captcha_input.strip():
                # 입력값이 있으면 반환
                return captcha_input.strip()
            
            time.sleep(0.5)  # 0.5초마다 확인
        
        return None
    
    def process_single_case(self, case, case_index):
        """단일 사건 처리"""
        case_number = case.get('사건번호', '')
        max_retry = self.max_retry.get()
        
        # 상태 업데이트
        self.update_case_status(case_index, "처리중", "orange")
        
        for attempt in range(max_retry + 1):
            try:
                self.log_message(f"📋 처리 시도 {attempt + 1}/{max_retry + 1}: {case_number}")
                
                # 1. 캡차 이미지 캡처 (임시 - 실제로는 Puppeteer에서)
                image_path = self.capture_captcha_image(case_number, attempt)
                
                # 2. 캡차 이미지 표시
                self.update_captcha_image(case_index, image_path)
                
                # 3. 캡차 입력 필드 활성화 및 대기
                self.update_case_status(case_index, "캡차입력", "blue")
                self.log_message(f"🔐 캡차 입력 대기: {case_number}")
                
                # 완료 버튼 활성화
                self.complete_btn.config(state=tk.NORMAL)
                
                # 사용자가 캡차를 입력할 때까지 대기
                captcha_input = self.wait_for_captcha_input(case_index, case_number)
                
                if captcha_input is None:
                    self.log_message(f"❌ 취소됨: {case_number}")
                    self.update_case_status(case_index, "취소", "red")
                    return False
                
                # 3. 캡차 입력 검증 (임시 - 실제로는 웹사이트에서)
                if self.validate_captcha(captcha_input):
                    self.log_message(f"✅ 캡차 검증 성공: {case_number}")
                    self.update_case_status(case_index, "처리중", "orange")
                    # 4. 실제 사건 처리 (Puppeteer 로직 호출)
                    result_data = self.execute_case_processing(case, captcha_input)
                    if result_data:
                        self.update_case_status(case_index, "완료", "green")
                        # 5. 구글 시트에 결과 저장 (진행내용 데이터 포함)
                        self.save_to_google_sheets(case, result_data)
                    else:
                        self.update_case_status(case_index, "실패", "red")
                    return bool(result_data)
                else:
                    self.log_message(f"❌ 캡차 검증 실패: {case_number} (시도 {attempt + 1})")
                    self.update_case_status(case_index, f"재시도{attempt + 1}", "yellow")
                    if attempt < max_retry:
                        time.sleep(self.retry_delay.get())
                    continue
                    
            except Exception as e:
                self.log_message(f"❌ 오류: {case_number} - {e}")
                self.update_case_status(case_index, "오류", "red")
                if attempt < max_retry:
                    time.sleep(self.retry_delay.get())
                continue
        
        self.log_message(f"❌ 최대 재시도 초과: {case_number}")
        self.update_case_status(case_index, "실패", "red")
        return False
    
    def capture_captcha_image(self, case_number, defendant, court, attempt):
        """캡차 이미지 캡처 (실제 Puppeteer 실행)"""
        try:
            self.log_message(f"🔐 캡차 이미지 캡처 시작: {case_number} (법원: {court})")
            
            # Puppeteer를 통한 실시간 캡차 이미지 캡처
            import subprocess
            import json
            
            # Puppeteer 실행을 위한 명령어 (캡차 이미지 캡처 전용) - 법원 정보 포함!
            cmd = ["node", "src/single-case-captcha.js", case_number, defendant, court]
            self.log_message(f"🚀 명령어: node src/single-case-captcha.js {case_number} {defendant} {court}")
            
            # Puppeteer 실행 (비동기로 실행하여 캡차 이미지만 캡처)
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='ignore')
            
            # stdout을 실시간으로 읽기
            image_path = None
            self.log_message(f"🔍 Puppeteer 출력 실시간 모니터링 시작: {case_number}")
            
            # 타임아웃 설정 (최대 90초 대기 - 네트워크 지연 고려)
            import time
            start_time = time.time()
            timeout = 90
            
            ws_url = None
            line_count = 0
            ws_url_found = False
            
            while time.time() - start_time < timeout:
                line = process.stdout.readline()
                if not line:
                    # EOF이지만 WS URL을 이미 받았으면 OK
                    if ws_url_found:
                        break
                    # 아직 못 받았으면 조금 더 대기
                    time.sleep(0.1)
                    continue
                
                line_count += 1
                
                # 중요한 출력만 로그 표시 (매 줄이 아닌 중요 정보만!)
                # GUI_IMAGE_PATH 찾기
                if 'GUI_IMAGE_PATH:' in line:
                    image_path = line.split('GUI_IMAGE_PATH: ')[1].strip()
                    self.log_message(f"🖼️ 이미지 경로 발견: {image_path}")
                
                # BROWSER_WS_URL 찾기 (브라우저 재연결용)
                elif 'BROWSER_WS_URL:' in line:
                    ws_url = line.split('BROWSER_WS_URL: ')[1].strip()
                    self.log_message(f"🔗 브라우저 WebSocket URL 저장: {case_number}")
                    # 브라우저 WebSocket URL 저장
                    self.browser_ws_urls[case_number] = ws_url
                    # 브라우저 프로세스도 저장 (종료 방지)
                    self.browser_processes[case_number] = process
                    self.log_message(f"🔒 브라우저 프로세스 저장 완료: {case_number}")
                    # 프로세스는 백그라운드에서 계속 실행됨
                    break
                
                # 에러 메시지만 표시
                elif 'ERROR' in line.upper() or '❌' in line or 'FAIL' in line.upper():
                    self.log_message(f"⚠️ Puppeteer 오류: {line.strip()}")
            
            # 브라우저를 종료하지 않고 유지 (사용자 입력 대기)
            self.log_message(f"🔒 브라우저 유지: {case_number} (사용자 입력 대기)")
            # process.wait() 제거 - 브라우저를 종료하지 않음
            
            if image_path and os.path.exists(image_path):
                self.log_message(f"✅ 새로운 캡차 이미지 캡처 성공: {image_path}")
                file_size = os.path.getsize(image_path)
                self.log_message(f"🔍 이미지 파일 확인: {image_path} ({file_size} bytes)")
                self.log_message(f"🖼️ GUI에 이미지 표시 준비 완료: {case_number}")
                return image_path
            else:
                self.log_message(f"❌ 캡차 이미지 캡처 실패: {case_number}")
                return None
                
        except subprocess.TimeoutExpired:
            self.log_message(f"⏰ Puppeteer 실행 시간 초과: {case_number}")
            return None
        except Exception as e:
            self.log_message(f"❌ 캡차 이미지 캡처 오류: {e}")
            return None
    
    def validate_captcha(self, captcha_input):
        """캡차 입력 검증 (임시 구현)"""
        # 실제로는 여기서 웹사이트에 캡차 입력 후 응답 확인
        # 임시로 랜덤 성공/실패
        import random
        return random.choice([True, True, False])  # 66% 성공률
    
    def execute_case_processing_with_captcha(self, case, case_index):
        """캡차 이미지만 캡처하고 GUI에 표시"""
        try:
            case_number = case.get('사건번호', '')
            defendant = case.get('피고', '')
            court = case.get('법원', '')
            
            self.log_message(f"🔄 처리 시작: {case_number} (법원: {court})")
            
            # 1. 먼저 캡차 이미지만 캡처 (법원 정보 포함!)
            self.log_message(f"📸 캡차 이미지 캡처 중: {case_number}")
            image_path = self.capture_captcha_image(case_number, defendant, court, 0)
            
            if image_path:
                # 2. GUI에 캡차 이미지 표시
                self.update_captcha_image(case_index, image_path)
                self.update_case_status(case_index, "캡차입력", "blue")
                self.log_message(f"🔐 캡차 입력 대기: {case_number}")
                
                # 3. 완료 버튼 활성화
                self.complete_btn.config(state=tk.NORMAL)
                self.log_message(f"✅ 캡차 입력 완료 버튼 활성화됨")
                
                return True
            else:
                self.log_message(f"❌ 캡차 이미지 캡처 실패: {case_number}")
                return False
                
        except Exception as e:
            self.log_message(f"❌ 처리 오류: {case_number} - {e}")
            return False

    def parse_puppeteer_result(self, stdout):
        """Puppeteer 실행 결과 파싱"""
        try:
            # GUI_IMAGE_PATH 찾기
            image_path = None
            for line in stdout.split('\n'):
                if 'GUI_IMAGE_PATH:' in line:
                    image_path = line.split('GUI_IMAGE_PATH: ')[1].strip()
                    break
            
            # JSON 결과가 있는지 확인
            if 'case_result_' in stdout:
                # JSON 파일에서 결과 읽기
                result_files = glob.glob("results/case_result_*.json")
                if result_files:
                    latest_file = max(result_files, key=os.path.getctime)
                    with open(latest_file, 'r', encoding='utf-8') as f:
                        result_data = json.load(f)
                    if image_path:
                        result_data['image_path'] = image_path
                    return result_data
            
            return {"success": True, "message": "처리 완료", "image_path": image_path}
        except Exception as e:
            self.log_message(f"❌ 결과 파싱 오류: {e}")
            return {"success": False, "message": str(e)}

    def execute_case_processing(self, case, captcha_input):
        """실제 Puppeteer로 사건 처리 실행"""
        try:
            case_number = case.get('사건번호', '')
            defendant = case.get('피고', '')
            court = case.get('법원', '')
            
            self.log_message(f"🔄 Puppeteer로 사건 처리 중: {case_number}")
            self.log_message(f"📋 사건 정보 - 피고: {defendant}, 법원: {court}")
            self.log_message(f"🔐 캡차 입력: {captcha_input}")
            
            # WebSocket 재연결 시에는 Chrome 프로세스를 유지해야 함!
            # (기존 브라우저 유지 중)
            if case_number not in self.browser_ws_urls:
                self.log_message(f"⚠️ 새 브라우저 시작 (WebSocket URL 없음)")
            
            # Puppeteer 실행을 위한 명령어 (진행내용 추출 포함)
            import subprocess
            cmd = ["node", "src/index.js", "--single-case", case_number, "--defendant", defendant, "--court", court, "--captcha", captcha_input]
            
            # WebSocket URL이 있으면 추가 (브라우저 재연결)
            if case_number in self.browser_ws_urls:
                ws_url = self.browser_ws_urls[case_number]
                cmd.extend(["--browser-ws-url", ws_url])
                self.log_message(f"🔗 기존 브라우저 재연결: {case_number}")
            else:
                self.log_message(f"⚠️ WebSocket URL 없음 - 새 브라우저 시작")
            
            self.log_message(f"🚀 명령어 실행: {' '.join(cmd)}")
            self.log_message(f"⏳ Puppeteer 실행 중... (최대 3분 대기)")
            
            # Puppeteer 실행 (중지 가능한 Popen 사용)
            self.log_message(f"🔄 [DEBUG] subprocess.Popen 실행 시작")
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='ignore', bufsize=1)
            
            # 출력을 실시간으로 수집
            import time
            start_time = time.time()
            timeout = 180
            
            stdout_lines = []
            stderr_lines = []
            
            # 실시간으로 출력 읽기
            while time.time() - start_time < timeout:
                # 중지 플래그 확인
                if not self.processing:
                    self.log_message(f"⏹️ [DEBUG] 중지 감지 - 프로세스 종료 중")
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except:
                        process.kill()
                    self.log_message(f"⏹️ 프로세스 강제 종료됨")
                    return False
                
                # stdout 실시간 읽기
                line = process.stdout.readline()
                if line:
                    line = line.strip()
                    stdout_lines.append(line)
                    # 중요한 로그만 표시
                    if line and any(keyword in line for keyword in ['✅', '❌', '⚠️', '🔐', '📄', '📊', '검색', '진행내용', 'DEBUG', 'ERROR', 'STEP']):
                        self.log_message(f"[Puppeteer] {line}")
                
                # 프로세스 종료 확인
                if process.poll() is not None:
                    # 나머지 출력 모두 읽기
                    for line in process.stdout:
                        line = line.strip()
                        if line:
                            stdout_lines.append(line)
                            if any(keyword in line for keyword in ['✅', '❌', '⚠️', '🔐', '📄', '📊', '검색', '진행내용', 'DEBUG', 'ERROR', 'STEP']):
                                self.log_message(f"[Puppeteer] {line}")
                    # stderr도 읽기
                    stderr_output = process.stderr.read()
                    if stderr_output:
                        stderr_lines = stderr_output.split('\n')
                    break
                
                time.sleep(0.01)  # 10ms 대기 (CPU 사용률 낮추기)
            
            # 타임아웃 체크
            if process.poll() is None:
                self.log_message(f"⏰ 타임아웃 - 프로세스 강제 종료")
                process.kill()
                return False
            
            returncode = process.returncode
            self.log_message(f"🔄 [DEBUG] subprocess.Popen 완료 (코드: {returncode})")
            
            # stdout_lines와 stderr_lines는 이미 수집됨
            
            if returncode == 0:
                self.log_message(f"✅ Puppeteer 처리 성공: {case_number}")
                
                # 결과 JSON 파일에서 진행내용 데이터 추출
                self.log_message(f"🔍 결과 파일에서 진행내용 추출 중...")
                progress_data = self.extract_progress_from_result(case_number)
                if progress_data:
                    self.log_message(f"📊 진행내용 데이터 추출: {len(progress_data)}개 행")
                    return progress_data
                else:
                    self.log_message(f"⚠️ 진행내용 데이터 없음: {case_number}")
                    return True  # 처리는 성공했지만 데이터는 없음
            else:
                self.log_message(f"❌ Puppeteer 처리 실패: {case_number} (종료 코드: {returncode})")
                if stderr_lines:
                    self.log_message(f"❌ 오류 메시지:")
                    for line in stderr_lines[:10]:  # 최대 10줄만
                        if line.strip():
                            self.log_message(f"  {line.strip()}")
                return False
                
        except Exception as e:
            self.log_message(f"❌ Puppeteer 실행 오류: {case_number} - {e}")
            return False
    
    def extract_progress_from_result(self, case_number):
        """결과 JSON 파일에서 진행내용 데이터 추출"""
        try:
            import json
            import glob
            import os
            
            # results 디렉토리에서 해당 사건의 결과 파일 찾기
            results_dir = "results"
            pattern = os.path.join(results_dir, f"case_result_*{case_number}*.json")
            result_files = glob.glob(pattern)
            
            if not result_files:
                self.log_message(f"⚠️ 결과 파일 없음: {case_number}")
                return None
            
            # 가장 최근 파일 선택
            latest_file = max(result_files, key=os.path.getctime)
            
            with open(latest_file, 'r', encoding='utf-8') as f:
                result_data = json.load(f)
            
            # 진행내용 데이터 추출
            progress_data = result_data.get('progressData', [])
            return progress_data
            
        except Exception as e:
            self.log_message(f"❌ 진행내용 데이터 추출 오류: {e}")
            return None
    
    def apply_text_colors(self, worksheet, color_info):
        """텍스트 색상 적용"""
        try:
            requests = []
            
            for info in color_info:
                row_idx = info['row']
                
                # RGB 색상 변환 함수
                def rgb_to_google_color(rgb_string):
                    if not rgb_string or not rgb_string.startswith('rgb'):
                        return None
                    # "rgb(255, 0, 0)" -> [255, 0, 0]
                    rgb = rgb_string.replace('rgb(', '').replace(')', '').split(',')
                    r, g, b = [int(x.strip()) / 255.0 for x in rgb]
                    return {"red": r, "green": g, "blue": b}
                
                # 각 셀에 색상 적용
                for col_idx, color_key in enumerate(['dateColor', 'contentColor', 'resultColor', 'documentColor']):
                    color_rgb = info.get(color_key)
                    if color_rgb:
                        google_color = rgb_to_google_color(color_rgb)
                        if google_color:
                            requests.append({
                                "repeatCell": {
                                    "range": {
                                        "sheetId": worksheet.id,
                                        "startRowIndex": row_idx - 1,
                                        "endRowIndex": row_idx,
                                        "startColumnIndex": col_idx,
                                        "endColumnIndex": col_idx + 1
                                    },
                                    "cell": {
                                        "userEnteredFormat": {
                                            "textFormat": {
                                                "foregroundColor": google_color
                                            }
                                        }
                                    },
                                    "fields": "userEnteredFormat.textFormat.foregroundColor"
                                }
                            })
            
            # 색상 일괄 적용
            if requests:
                body = {"requests": requests}
                worksheet.spreadsheet.batch_update(body)
                
        except Exception as e:
            self.log_message(f"⚠️ 색상 적용 실패: {e}")
    
    def load_update_history(self):
        """로컬 업데이트 기록 로드"""
        try:
            history_file = 'update_history.json'
            if os.path.exists(history_file):
                with open(history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            self.log_message(f"⚠️ 업데이트 기록 로드 실패: {e}")
            return {}
    
    def save_update_history(self, history):
        """로컬 업데이트 기록 저장"""
        try:
            history_file = 'update_history.json'
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.log_message(f"⚠️ 업데이트 기록 저장 실패: {e}")
    
    def update_case_timestamp(self, case, original_index=None, row_count=0):
        """사건 업데이트 타임스탬프 및 행 개수 기록, GUI 갱신"""
        try:
            history = self.load_update_history()
            case_number = case.get('사건번호', '')
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 이전 행 개수 가져오기
            old_data = history.get(case_number, {})
            if isinstance(old_data, str):  # 구버전 호환성 (문자열만 저장된 경우)
                old_row_count = 0
            else:
                old_row_count = old_data.get('row_count', 0)
            
            # 새로운 데이터 저장 (시간 + 행 개수)
            history[case_number] = {
                'last_update': current_time,
                'row_count': row_count
            }
            self.save_update_history(history)
            
            # 새로 추가된 행 개수 계산
            new_rows = row_count - old_row_count if row_count > old_row_count else 0
            
            self.log_message(f"📝 업데이트 기록: {case_number} - {current_time} (행: {row_count}, 신규: +{new_rows})")
            
            # GUI 업데이트 (날짜 + D+0 + 새 행 개수 표시)
            if original_index is not None:
                date_str = current_time.split(' ')[0]  # 날짜만 추출
                new_rows_text = f" (+{new_rows})" if new_rows > 0 else ""
                
                def update_labels():
                    # D+n 라벨 업데이트
                    if original_index in self.case_update_labels:
                        display_text = f"D+0{new_rows_text}"
                        color = "#28A745" if new_rows > 0 else "#0D6EFD"
                        self.case_update_labels[original_index].config(text=display_text, fg=color)
                    
                    # 날짜 라벨 업데이트 또는 생성
                    if original_index in self.case_update_date_labels:
                        if self.case_update_date_labels[original_index]:
                            self.case_update_date_labels[original_index].config(text=date_str)
                        else:
                            # 날짜 라벨이 없으면 생성
                            if original_index in self.case_update_labels:
                                parent = self.case_update_labels[original_index].master
                                new_date_label = tk.Label(parent, text=date_str, 
                                                        font=("맑은 고딕", 7), fg="#6C757D",
                                                        bg=parent['bg'], anchor=tk.CENTER)
                                new_date_label.pack(before=self.case_update_labels[original_index])
                                self.case_update_date_labels[original_index] = new_date_label
                
                self.root.after(0, update_labels)
            
        except Exception as e:
            self.log_message(f"⚠️ 업데이트 기록 실패: {e}")
    
    def get_days_since_update(self, case):
        """최근 업데이트 이후 경과일수 조회 (D+n 형식)"""
        try:
            history = self.load_update_history()
            case_number = case.get('사건번호', '')
            
            if case_number in history:
                data = history[case_number]
                
                # 구버전 호환성 (문자열만 저장된 경우)
                if isinstance(data, str):
                    last_update_str = data
                else:
                    last_update_str = data.get('last_update', '')
                
                if last_update_str:
                    last_update = datetime.strptime(last_update_str, '%Y-%m-%d %H:%M:%S')
                    current = datetime.now()
                    days_diff = (current - last_update).days
                    return f"D+{days_diff}"
            
            return "-"
        except Exception as e:
            return "-"
    
    def format_update_timestamp_rows(self, worksheet, start_row):
        """업데이트 일시 행 포맷팅 (좌측 정렬)"""
        try:
            requests = []
            
            # 두 행 모두 좌측 정렬
            for i in range(2):
                requests.append({
                    "repeatCell": {
                        "range": {
                            "sheetId": worksheet.id,
                            "startRowIndex": start_row + i - 1,
                            "endRowIndex": start_row + i,
                            "startColumnIndex": 0,
                            "endColumnIndex": 4
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "horizontalAlignment": "LEFT"
                            }
                        },
                        "fields": "userEnteredFormat.horizontalAlignment"
                    }
                })
            
            body = {"requests": requests}
            worksheet.spreadsheet.batch_update(body)
            
        except Exception as e:
            self.log_message(f"⚠️ 업데이트 일시 포맷팅 실패: {e}")
    
    def auto_resize_columns(self, worksheet):
        """열 너비 자동 조정"""
        try:
            requests = []
            
            # 모든 열 자동 조정
            requests.append({
                "autoResizeDimensions": {
                    "dimensions": {
                        "sheetId": worksheet.id,
                        "dimension": "COLUMNS",
                        "startIndex": 0,
                        "endIndex": 4  # A-D 컬럼 (0-3)
                    }
                }
            })
            
            # A열 (일자 열) - 업데이트 일시 텍스트를 위해 충분히 크게
            requests.append({
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": worksheet.id,
                        "dimension": "COLUMNS",
                        "startIndex": 0,
                        "endIndex": 1
                    },
                    "properties": {
                        "pixelSize": 200  # 200픽셀로 설정
                    },
                    "fields": "pixelSize"
                }
            })
            
            # B열 (내용 열) - 긴 텍스트를 위해 더 크게
            requests.append({
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": worksheet.id,
                        "dimension": "COLUMNS",
                        "startIndex": 1,
                        "endIndex": 2
                    },
                    "properties": {
                        "pixelSize": 500  # 500픽셀로 설정
                    },
                    "fields": "pixelSize"
                }
            })
            
            body = {"requests": requests}
            worksheet.spreadsheet.batch_update(body)
            
        except Exception as e:
            self.log_message(f"⚠️ 열 자동 조정 실패: {e}")
    
    def save_to_google_sheets(self, case, result_data):
        """구글 시트에 결과 저장"""
        try:
            case_number = case.get('사건번호', '')
            self.log_message(f"💾 [DEBUG] save_to_google_sheets 시작: {case_number}")
            self.log_message(f"💾 [DEBUG] result_data 타입: {type(result_data)}, 길이: {len(result_data) if isinstance(result_data, list) else 'N/A'}")
            self.log_message(f"💾 구글 시트에 저장 중: {case_number}")
            
            # 구글 시트 연결
            self.log_message(f"💾 [DEBUG] 구글 시트 모듈 import 중")
            import gspread
            from google.oauth2.service_account import Credentials
            
            # 서비스 계정 인증
            self.log_message(f"💾 [DEBUG] 서비스 계정 인증 중")
            scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
            creds = Credentials.from_service_account_file('./api/certification/service-account.json', scopes=scope)
            client = gspread.authorize(creds)
            
            # 스프레드시트 열기
            self.log_message(f"💾 [DEBUG] 스프레드시트 열기 중")
            spreadsheet = client.open('case-ing-test')
            
            # 결과 워크시트 생성 또는 열기
            # 시트명: 피고_비고_사건번호_법원
            defendant = case.get('피고', '')
            remark = case.get('비고', '')
            court = case.get('법원', '')
            
            if remark:
                worksheet_name = f"{defendant}_{remark}_{case_number}_{court}"
            else:
                worksheet_name = f"{defendant}_{case_number}_{court}"
            
            self.log_message(f"💾 [DEBUG] 워크시트 찾기/생성 중: {worksheet_name}")
            try:
                worksheet = spreadsheet.worksheet(worksheet_name)
                self.log_message(f"💾 [DEBUG] 기존 워크시트 사용")
            except gspread.WorksheetNotFound:
                worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows=100, cols=10)
                self.log_message(f"💾 [DEBUG] 새 워크시트 생성됨")
            
            # 기존 데이터에서 마지막 업데이트 시간 추출 (초기화 전)
            self.log_message(f"💾 [DEBUG] 이전 업데이트 시간 확인 중")
            previous_update_time = None
            try:
                # 모든 행 읽기
                all_values = worksheet.get_all_values()
                if len(all_values) > 0:
                    # 뒤에서부터 "업데이트 일시" 찾기
                    for row in reversed(all_values):
                        if len(row) >= 2 and row[0] == '업데이트 일시' and row[1]:
                            previous_update_time = str(row[1]).strip()
                            self.log_message(f"💾 [DEBUG] 이전 업데이트 시간: {previous_update_time}")
                            break
            except Exception as e:
                self.log_message(f"💾 [DEBUG] 이전 업데이트 시간 확인 실패: {e}")
            
            # 워크시트 초기화 (기존 데이터 삭제)
            self.log_message(f"💾 [DEBUG] 워크시트 초기화 중")
            worksheet.clear()
            
            # 헤더 추가 (진행내용 형식: 일자, 내용, 결과, 공시문)
            self.log_message(f"💾 [DEBUG] 헤더 추가 중")
            headers = ['일자', '내용', '결과', '공시문']
            worksheet.append_row(headers)
            self.log_message(f"💾 [DEBUG] 헤더 추가 완료")
            
            # 진행내용 데이터가 있는 경우 상세 저장
            if isinstance(result_data, list) and len(result_data) > 0:
                self.log_message(f"💾 [DEBUG] 진행내용 데이터 저장 시작: {len(result_data)}개 행")
                
                # 모든 행을 한 번에 저장 (API 요청 1번으로 최적화)
                all_rows = []
                color_info = []  # 색상 정보 저장
                
                for idx, progress_row in enumerate(result_data):
                    row_data = [
                        progress_row.get('date', ''),      # 일자
                        progress_row.get('content', ''),   # 내용
                        progress_row.get('result', ''),    # 결과
                        progress_row.get('document', '')   # 공시문
                    ]
                    all_rows.append(row_data)
                    
                    # 색상 정보 저장 (행 번호는 헤더 다음부터이므로 idx+2)
                    color_info.append({
                        'row': idx + 2,
                        'dateColor': progress_row.get('dateColor'),
                        'contentColor': progress_row.get('contentColor'),
                        'resultColor': progress_row.get('resultColor'),
                        'documentColor': progress_row.get('documentColor')
                    })
                
                # 한 번에 저장 (append_rows - 복수형!)
                self.log_message(f"💾 [DEBUG] 한 번에 {len(all_rows)}개 행 저장 중...")
                worksheet.append_rows(all_rows, value_input_option='USER_ENTERED')
                self.log_message(f"💾 [DEBUG] 모든 행 한 번에 저장 완료")
                
                # 색상 적용
                self.log_message(f"🎨 [DEBUG] 텍스트 색상 적용 중...")
                self.apply_text_colors(worksheet, color_info)
                self.log_message(f"🎨 [DEBUG] 텍스트 색상 적용 완료")
                
                self.log_message(f"✅ 진행내용 {len(result_data)}개 행 저장 완료")
            else:
                # 데이터가 없는 경우
                self.log_message(f"⚠️ 진행내용 데이터가 없습니다")
            
            # 하단에 업데이트 시간 기록 추가
            self.log_message(f"💾 [DEBUG] 업데이트 시간 기록 추가 중")
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 빈 줄 5개 추가
            empty_rows = [['', '', '', ''] for _ in range(5)]
            worksheet.append_rows(empty_rows, value_input_option='USER_ENTERED')
            
            # 현재 행 번호 계산 (헤더 1 + 데이터 + 빈 줄 5)
            current_row = 1 + len(result_data) + 5 + 1
            
            # 업데이트 일시 추가
            update_rows = [
                ['업데이트 일시', current_time, '', ''],
                ['최근 과거 업데이트', previous_update_time if previous_update_time else '', '', '']
            ]
            worksheet.append_rows(update_rows, value_input_option='USER_ENTERED')
            
            # 업데이트 일시 행 좌측 정렬
            self.format_update_timestamp_rows(worksheet, current_row)
            
            if previous_update_time:
                self.log_message(f"💾 [DEBUG] 이전 업데이트 시간 기록: {previous_update_time}")
            else:
                self.log_message(f"💾 [DEBUG] 이전 업데이트 없음 (빈 칸)")
            
            self.log_message(f"💾 [DEBUG] 업데이트 시간 기록 완료")
            
            # 열 너비 자동 조정
            self.log_message(f"📏 [DEBUG] 열 너비 자동 조정 중...")
            self.auto_resize_columns(worksheet)
            self.log_message(f"📏 [DEBUG] 열 너비 자동 조정 완료")
            
            self.log_message(f"💾 [DEBUG] save_to_google_sheets 완료 직전")
            self.log_message(f"✅ 구글 시트 저장 완료: {worksheet_name}")
            self.log_message(f"💾 [DEBUG] save_to_google_sheets 반환 전 - 행 개수: {len(result_data)}")
            return len(result_data)  # 저장된 행 개수 반환
            
        except Exception as e:
            self.log_message(f"❌ 구글 시트 저장 실패: {e}")
            self.log_message(f"❌ [DEBUG] 예외 타입: {type(e).__name__}")
            import traceback
            self.log_message(f"❌ [DEBUG] 예외 스택: {traceback.format_exc()}")
            return False
    
    
    def update_case_status(self, case_index, status, color, emoji=""):
        """사건 상태 업데이트 (이모지 포함) (Thread-Safe)"""
        def _update():
            if case_index in self.case_status:
                display_text = f"{emoji} {status}" if emoji else status
                self.case_status[case_index].config(text=display_text, fg=color)
                
                # 처리 중인 사건 하이라이트
                if case_index in self.case_frames:
                    if status == "처리중":
                        # 노란색 배경으로 하이라이트
                        self.case_frames[case_index].config(bg="#FFF3CD")
                        # 프레임 내 모든 위젯도 배경색 변경
                        for widget in self.case_frames[case_index].winfo_children():
                            try:
                                widget.config(bg="#FFF3CD")
                            except:
                                pass
                    elif status.startswith("완료"):
                        # 연한 초록색 배경
                        self.case_frames[case_index].config(bg="#D4EDDA")
                        for widget in self.case_frames[case_index].winfo_children():
                            try:
                                widget.config(bg="#D4EDDA")
                            except:
                                pass
                    elif status.startswith("실패") or status.startswith("오류"):
                        # 연한 빨간색 배경
                        self.case_frames[case_index].config(bg="#F8D7DA")
                        for widget in self.case_frames[case_index].winfo_children():
                            try:
                                widget.config(bg="#F8D7DA")
                            except:
                                pass
        
        # 메인 스레드에서 실행
        self.root.after(0, _update)
    
    def update_captcha_image(self, case_index, image_path):
        """캡차 이미지 업데이트"""
        if case_index not in self.case_images:
            self.log_message(f"❌ 캡차 이미지 업데이트 실패: 인덱스 {case_index} 없음")
            return False
        
        try:
            image_label = self.case_images[case_index]
            
            if image_path and os.path.exists(image_path):
                # 파일 크기 확인
                file_size = os.path.getsize(image_path)
                self.log_message(f"🔍 이미지 파일 확인: {image_path} ({file_size} bytes)")
                
                from PIL import Image, ImageTk
                # 이미지 로드 및 리사이즈 (적절한 크기)
                img = Image.open(image_path)
                img = img.resize((200, 60), Image.Resampling.LANCZOS)  # 적절한 크기로 조정
                photo = ImageTk.PhotoImage(img)
                
                # 이미지 표시 (적절한 크기)
                image_label.config(image=photo, text="", width=200, height=60)
                image_label.image = photo  # 참조 유지
                
                # GUI 강제 업데이트
                self.root.update()
                self.log_message(f"🖼️ 캡차 이미지 업데이트 성공: 인덱스 {case_index}")
                self.log_message(f"✅ GUI에 캡차 이미지 표시 완료: {image_path}")
                return True
            else:
                self.log_message(f"⚠️ 캡차 이미지 없음: {image_path}")
                image_label.config(image="", text="이미지없음", fg="red")
                return False
                
        except Exception as e:
            self.log_message(f"❌ 이미지 업데이트 오류: {e}")
            if case_index in self.case_images:
                self.case_images[case_index].config(image="", text="오류", fg="red")
            return False
    
    def wait_for_captcha_input(self, case_index, timeout_seconds=300):
        """캡차 입력 대기 (최대 timeout_seconds초)"""
        if case_index not in self.case_inputs:
            return None
        
        # 입력 필드 활성화
        captcha_var = self.case_inputs[case_index]
        
        # 사용자가 입력할 때까지 대기
        start_time = time.time()
        
        while time.time() - start_time < timeout_seconds:
            if not self.processing:  # 처리 중지됨
                return None
            
            # 입력값 확인
            captcha_text = captcha_var.get().strip()
            if len(captcha_text) == 6:
                # 입력 필드 비우기
                captcha_var.set("")
                return captcha_text
            
            time.sleep(0.5)  # 0.5초마다 확인
        
        # 시간 초과
        self.log_message(f"⏰ 캡차 입력 시간 초과: {timeout_seconds}초")
        return None
    
    def find_case_index(self, case_number):
        """사건번호로 사건 인덱스 찾기"""
        for i, case in enumerate(self.case_list):
            if case.get('사건번호', '') == case_number:
                return i
        return -1
    
    def processing_completed(self):
        """처리 완료 후 UI 업데이트"""
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.log_message("🎉 모든 사건 처리 완료!")
        messagebox.showinfo("완료", "모든 사건 처리가 완료되었습니다.")
    
    def log_message(self, message):
        """로그 메시지 추가 (Thread-Safe)"""
        def _log():
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_entry = f"[{timestamp}] {message}\n"
            self.status_text.insert(tk.END, log_entry)
            self.status_text.see(tk.END)
        
        # 메인 스레드에서 실행
        self.root.after(0, _log)
    
    def update_progress(self, percentage, status_text=""):
        """진행률 업데이트 (Thread-Safe)"""
        def _update():
            try:
                # 진행률 바 업데이트
                self.progress_var.set(percentage)
                
                # 상태 텍스트 업데이트
                if status_text:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    status_entry = f"[{timestamp}] {status_text}\n"
                    self.status_text.insert(tk.END, status_entry)
                    self.status_text.see(tk.END)
                
            except Exception as e:
                print(f"진행률 업데이트 오류: {e}")
        
        # 메인 스레드에서 실행
        self.root.after(0, _update)
    
    def run(self):
        """GUI 실행"""
        self.root.mainloop()

def main():
    """메인 함수"""
    print("=== 일괄 처리 GUI 시작 ===")
    
    gui = BatchProcessingGUI()
    
    # GUI 구성
    root = gui.create_window()
    
    # 헤더 (상단 전체)
    gui.create_header(root)
    
    # 메인 컨테이너 (좌측 + 우측)
    main_container = tk.Frame(root, bg="#2C3E50")
    main_container.pack(fill=tk.BOTH, expand=True)
    
    # 좌측 패널
    left_panel = tk.Frame(main_container, bg="#2C3E50")
    left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    # 우측 패널 (진행상황)
    right_panel = tk.Frame(main_container, bg="#ECF0F1", width=400)
    right_panel.pack(side=tk.RIGHT, fill=tk.BOTH)
    right_panel.pack_propagate(False)  # 크기 고정
    
    # 좌측에 패널들 배치
    gui.create_control_panel(left_panel)
    gui.create_settings_panel(left_panel)
    gui.create_case_list_panel(left_panel)
    
    # 우측에 진행상황 배치
    gui.create_progress_panel(right_panel)
    
    # GUI 실행
    gui.run()

if __name__ == "__main__":
    main()

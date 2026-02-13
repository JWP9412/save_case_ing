#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
일괄 처리용 GUI 생성기
====================

역할: 여러 사건을 한번에 처리할 수 있는 GUI 생성.
호출 시점: python batch_gui_maker.py 로 실행하면 이 파일의 main() 이 먼저 돌고, BatchProcessingGUI 가 창을 띄웁니다.

기능:
- 구글 시트에서 사건 목록 로드
- 사건 선택 (체크박스)
- 처리 옵션 설정
- 실시간 진행상황 모니터링
- 캡차 재시도 시스템

사용법: python main.py (진입점은 main.py)

프로그램 구조 설명:
------------------
1. load_google_sheet_data(): 구글 시트에서 사건 목록을 읽어오는 함수
2. CaptchaInputDialog: 캡차 입력을 받는 팝업 창 클래스
3. BatchProcessingGUI: 메인 GUI 클래스
   - create_window(): 메인 창 생성
   - create_header(): 상단 헤더 영역 생성
   - create_control_panel(): 버튼들이 있는 제어 패널 생성
   - create_settings_panel(): 병렬 처리 수 등 설정 패널 생성
   - create_case_list_panel(): 사건 목록을 표시하는 패널 생성
   - create_progress_panel(): 진행상황을 표시하는 패널 생성
   - load_google_sheet(): 구글 시트에서 사건 목록 로드
   - update_case_list_ui(): 사건 목록 UI 업데이트
   - start_batch_processing(): 캡차 이미지 로드 시작
   - process_all_captcha_inputs(): 모든 캡차 입력 처리
   - execute_case_processing(): Puppeteer로 실제 사건 처리
   - save_to_google_sheets(): 구글 시트에 결과 저장
"""

# ============================================================================
# 필요한 라이브러리 import (모듈 가져오기)
# ============================================================================
# tkinter: GUI를 만들기 위한 기본 라이브러리 (Python 기본 포함)
import tkinter as tk

# ttk: 더 예쁜 위젯들을 제공하는 확장 모듈
from tkinter import ttk, messagebox, scrolledtext

# CustomTkinter: 현대적인 디자인 (다크/라이트 모드 선택 가능)
import customtkinter as ctk

ctk.set_default_color_theme("blue")

# gspread: 구글 시트를 다루기 위한 라이브러리
import gspread

# json: JSON 파일을 읽고 쓰기 위한 라이브러리
import json

# threading: 여러 작업을 동시에 처리하기 위한 스레드 라이브러리
import threading

# time: 시간 관련 기능 (대기, 시간 측정 등)
import time

# subprocess: 다른 프로그램(Node.js 등)을 실행하기 위한 라이브러리
import subprocess

# os: 파일 시스템 관련 기능 (파일 존재 확인, 경로 등)
import os

# glob: 파일 패턴으로 여러 파일을 찾기 위한 라이브러리
import glob

# datetime: 날짜와 시간을 다루기 위한 라이브러리
from datetime import datetime

# THEME, COL_WIDTHS는 config.py에서 import (위에서 from config import THEME, COL_WIDTHS)

# ThreadPoolExecutor: 여러 작업을 병렬로 처리하기 위한 클래스
from concurrent.futures import ThreadPoolExecutor, as_completed

# config: 설정 상수 모음 (THEME, COL_WIDTHS, 열 순서 등)
import config
from config import (
    THEME,
    COL_WIDTHS,
    COL_NAMES,
    DEFAULT_COL_ORDER,
    COLUMN_ORDER_FILE,
    HEADER_IMAGE_PATH,
    HEADER_BG_COLOR,
)

# services.google_sheets: 구글 시트 서비스 모듈
from services.google_sheets import GoogleSheetsService, load_google_sheet_data

# services.puppeteer: Puppeteer 서비스 모듈
from services.puppeteer import PuppeteerService

# services.update_history: 업데이트 기록 파일 읽기/쓰기
from services import update_history as update_history_service

# sys: 시스템 관련 기능 (경로 추가 등)
import sys

# 현재 파일의 경로를 Python 경로에 추가 (다른 모듈 import를 위해)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ============================================================================
# 구글 시트 데이터 로드 함수
# ============================================================================
# 이 함수는 services/google_sheets.py로 이동되었습니다.
# 하위 호환성을 위해 여기서 import하여 사용합니다.
# load_google_sheet_data는 services/google_sheets.py에서 import됨

# 캡차 입력 팝업 창 (gui/captcha_dialog.py에서 분리됨)
from gui.captcha_dialog import CaptchaInputDialog

# tksheet: 구글 시트 뷰어/편집용 그리드 위젯
try:
    from tksheet import Sheet

    TKSHEET_AVAILABLE = True
except ImportError:
    TKSHEET_AVAILABLE = False
    Sheet = None


# ============================================================================
# 메인 GUI 클래스: BatchProcessingGUI
# ============================================================================
class BatchProcessingGUI:
    """
    일괄 처리 GUI를 관리하는 메인 클래스

    이 클래스는:
    - GUI 창을 생성하고 관리합니다
    - 구글 시트에서 사건 목록을 불러옵니다
    - 사용자가 선택한 사건들을 처리합니다
    - Puppeteer를 통해 웹 크롤링을 실행합니다
    - 결과를 구글 시트에 저장합니다
    """

    def __init__(self):
        """
        GUI 초기화 함수

        이 함수는 GUI를 만들기 전에 필요한 변수들을 미리 준비합니다.
        실제 GUI 창은 create_window() 함수에서 생성됩니다.
        """
        # ============================================================
        # GUI 관련 변수들
        # ============================================================
        # root: 메인 창 객체 (아직 생성 안 됨, create_window()에서 생성)
        self.root = None
        # case_list: 구글 시트에서 불러온 사건 목록 (리스트)
        # 예: [{'사건번호': '2023가합10019', '피고': '에이스', ...}, ...]
        self.case_list = []
        # selected_cases: 사용자가 선택한 사건들 (현재는 사용 안 함)
        self.selected_cases = []
        # processing: 현재 처리 중인지 여부를 나타내는 플래그 (True/False)
        # True면 처리 중, False면 대기 중
        self.processing = False
        # progress_var: 진행률 바의 값을 저장하는 변수 (0~100)
        self.progress_var = None
        # status_text: 로그를 표시하는 텍스트 위젯
        self.status_text = None
        # case_checkboxes: 각 사건의 체크박스 상태를 저장하는 딕셔너리
        # 예: {0: BooleanVar(True), 1: BooleanVar(False), ...}
        # 키는 사건 인덱스, 값은 체크박스 상태
        self.case_checkboxes = {}
        # header_select_all_var: 헤더 "전체 선택" 토글 체크박스 상태 (True=전체 선택, False=전체 해제)
        # create_window()에서 tk.Tk() 생성 후 초기화됨
        self.header_select_all_var = None
        # processing_thread: 백그라운드에서 처리 작업을 실행하는 스레드
        self.processing_thread = None

        # ============================================================
        # 브라우저 관련 변수들
        # ============================================================
        # browser_ws_urls: 각 사건의 브라우저 WebSocket URL을 저장
        # WebSocket URL은 브라우저를 재연결할 때 사용됩니다
        # 예: {'2023가합10019': 'ws://127.0.0.1:9222/...', ...}
        self.browser_ws_urls = {}
        # browser_processes: 각 사건의 Node.js 프로세스를 저장
        # 나중에 브라우저를 종료할 때 이 프로세스를 종료합니다
        # 예: {'2023가합10019': <subprocess.Popen object>, ...}
        self.browser_processes = {}

        # 정렬 상태 (사건 목록 컬럼 정렬용)
        # sort_column_index: 정렬 기준 컬럼 인덱스 (기본 9 = 최근 업데이트)
        self.sort_column_index = 8  # 최근 업데이트 (10열 기준)
        # sort_reverse: False = 오름차순(과거 날짜가 위), True = 내림차순
        self.sort_reverse = False
        # 열 너비 리사이즈 드래그 상태
        self._resize_col = None
        self._resize_start_x = None
        self._resize_start_width = None
        self._resize_current_width = None
        self.resize_guide_line = None
        # 열 표시 순서 (인덱스 0~9 리스트). update_case_list_ui에서 파일 로드 시 덮어씀
        self.col_order = list(DEFAULT_COL_ORDER)
        # 열 너비 (인덱스 0~9). update_case_list_ui에서 파일 로드 시 덮어씀
        self.col_widths = list(COL_WIDTHS)
        # tksheet 미설치 시 경고 메시지 세션당 1회만 표시
        self._tksheet_warned = False

        # ============================================================
        # 설정 옵션 변수들 (root 생성 후 초기화됨)
        # ============================================================
        # max_parallel: 동시에 처리할 수 있는 최대 사건 수 (기본값: 3)
        self.max_parallel = None
        # max_retry: 캡차 실패 시 최대 재시도 횟수 (기본값: 3)
        self.max_retry = None
        # retry_delay: 재시도 전 대기 시간(초) (기본값: 2초)
        self.retry_delay = None
        # 테마: "Dark" / "Light" / "System". create_window()에서 로드 후 적용
        self._appearance_mode = "Dark"
        self._theme_index = 1  # 0=라이트, 1=다크 (THEME 튜플 인덱스)

    def get_theme_color(self, key):
        """현재 테마에 맞는 색상 또는 폰트 반환. THEME 값이 (light, dark) 튜플이면 현재 모드 값 반환."""
        v = THEME.get(key)
        if (
            isinstance(v, tuple)
            and len(v) >= 2
            and isinstance(v[0], str)
            and v[0].startswith("#")
        ):
            return v[self._theme_index]
        return v

    def _load_theme_setting(self):
        """저장된 테마 설정 로드. "Dark" / "Light" / "System" 중 하나 반환."""
        path = getattr(config, "THEME_CONFIG_FILE", "theme_config.json")
        try:
            if os.path.isfile(path):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                mode = data.get("appearance_mode") or data.get("mode")
                if mode in ("Dark", "Light", "System"):
                    return mode
        except Exception:
            pass
        return "Dark"

    def _save_theme_setting(self, mode):
        """선택한 테마를 파일에 저장."""
        path = getattr(config, "THEME_CONFIG_FILE", "theme_config.json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"appearance_mode": mode}, f, indent=2)
        except Exception:
            pass

    def _apply_theme(self, mode):
        """테마 적용: set_appearance_mode 호출 후 _theme_index 갱신."""
        self._appearance_mode = mode
        ctk.set_appearance_mode(mode)
        effective = ctk.get_appearance_mode()
        self._theme_index = 1 if effective == "Dark" else 0

    def on_closing(self):
        """종료 처리"""
        if messagebox.askokcancel("종료", "프로그램을 종료하시겠습니까?"):
            # 진행상황(우측) 패널 너비 저장 (다음 실행 시 복원)
            if getattr(self, "right_panel", None) is not None:
                try:
                    if self.right_panel.winfo_exists():
                        w = self.right_panel.winfo_width()
                        path = getattr(
                            config, "RIGHT_PANEL_WIDTH_FILE", "right_panel_width.json"
                        )
                        with open(path, "w", encoding="utf-8") as f:
                            json.dump({"width": w}, f, indent=2)
                except Exception:
                    pass
            if hasattr(self, "puppeteer_service"):
                # 실행 중인 모든 프로세스 종료
                for process in list(self.puppeteer_service.running_processes.values()):
                    try:
                        process.terminate()
                    except:
                        pass
            self.root.destroy()

    def create_window(self):
        """메인 윈도우 생성 (CustomTkinter)"""
        # 저장된 테마 적용 (창 생성 전에 설정해야 함)
        saved_theme = self._load_theme_setting()
        self._apply_theme(saved_theme)

        self.root = ctk.CTk()
        self.root.title(f"{config.APP_TITLE} v{config.APP_VERSION}")
        w, h = config.WINDOW_WIDTH, config.WINDOW_HEIGHT
        self.root.geometry(f"{w}x{h}")
        self.root.resizable(True, True)

        # 종료 이벤트 바인딩
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # 모니터 정중앙 배치 (tk::PlaceWindow . center는 Windows/다중모니터에서 불안정하므로 수동 계산)
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

        # Tkinter 변수 초기화 (root 생성 후)
        self.header_select_all_var = tk.BooleanVar(value=False)

        # config.py에서 기본값 가져오기
        self.max_parallel = tk.IntVar(value=config.DEFAULT_MAX_PARALLEL)
        self.max_retry = tk.IntVar(value=config.DEFAULT_MAX_RETRY)
        self.retry_delay = tk.IntVar(value=config.DEFAULT_RETRY_DELAY)

        # ============================================================
        # 서비스 객체 생성
        # ============================================================
        # 구글 시트 서비스 (로그 콜백 함수 연결)
        self.google_sheets_service = GoogleSheetsService(log_callback=self.log_message)
        # Puppeteer 서비스 (로그 콜백 함수 연결)
        # processing_flag는 나중에 설정 (self.processing이 아직 생성되지 않았음)
        self.puppeteer_service = PuppeteerService(log_callback=self.log_message)
        # 증분 업데이트용 마지막 저장 항목 관리
        self.history_manager = update_history_service.HistoryManager()
        # 사건번호별 고정 프로필(인스턴스) 사용 시 동일 프로필 동시 접근 방지
        max_profiles = getattr(config, "MAX_PARALLEL_LIMIT", 20)
        self.profile_locks = [threading.Lock() for _ in range(max_profiles)]

        # processing_flag를 나중에 설정하기 위한 참조 저장
        # (start_processing에서 설정)

        return self.root

    def create_header(self, parent):
        """헤더 영역 생성 (CustomTkinter). 배너 이미지가 있으면 중앙에 표시, 여백은 배경색으로 채움."""
        header_bg = getattr(config, "HEADER_BG_COLOR", "#001A33")
        header_frame = ctk.CTkFrame(parent, fg_color=(header_bg, header_bg), height=120)
        header_frame.pack(fill=tk.X, padx=0, pady=0)
        header_frame.pack_propagate(False)

        banner_path = getattr(config, "HEADER_IMAGE_PATH", "./assets/title_banner.png")
        if not os.path.isabs(banner_path):
            base_dir = os.path.dirname(os.path.abspath(__file__))
            banner_path = os.path.normpath(os.path.join(base_dir, banner_path))
        if os.path.isfile(banner_path):
            try:
                if hasattr(self, "log_message"):
                    self.log_message(f"배너 경로: {banner_path}")
                from PIL import Image
                with Image.open(banner_path) as im:
                    bw, bh = im.size
                if bw <= 0 or bh <= 0:
                    if hasattr(self, "log_message"):
                        self.log_message("배너 이미지 로드 실패: 이미지 크기가 유효하지 않음")
                else:
                    # 배너 프레임 높이(120)에 맞춰 세로를 채우고, 가로는 비율 유지·최대 900으로 제한
                    banner_h = 120
                    max_banner_w = 900
                    scale = min(banner_h / bh, max_banner_w / bw)
                    w, h = int(bw * scale), int(bh * scale)
                    pil_img = Image.open(banner_path)
                    ctk_image = ctk.CTkImage(
                        light_image=pil_img,
                        dark_image=pil_img,
                        size=(w, h),
                    )
                    banner_label = ctk.CTkLabel(
                        header_frame,
                        text="",
                        image=ctk_image,
                    )
                    banner_label.pack(anchor=tk.CENTER, expand=False)
                    return header_frame
            except Exception as e:
                if hasattr(self, "log_message"):
                    self.log_message(f"배너 이미지 로드 실패: {banner_path} — {e}")
                else:
                    print(f"배너 이미지 로드 실패: {banner_path} — {e}")
        title_label = ctk.CTkLabel(
            header_frame,
            text=f"⚖️ {config.APP_TITLE}",
            font=ctk.CTkFont(family="맑은 고딕", size=26, weight="bold"),
            text_color="#ECF0F1",
        )
        title_label.pack(pady=(20, 5))
        subtitle_label = ctk.CTkLabel(
            header_frame,
            text=f"{config.APP_SUBTITLE} v{config.APP_VERSION}",
            font=ctk.CTkFont(family="맑은 고딕", size=13),
            text_color="#BDC3C7",
        )
        subtitle_label.pack(pady=(0, 15))
        return header_frame

    def create_control_panel(self, parent):
        """제어 패널 생성 (CustomTkinter)"""
        control_frame = ctk.CTkFrame(
            parent, fg_color=self.get_theme_color("bg_primary")
        )
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        ctk.CTkLabel(
            control_frame,
            text="🎛️ 제어 패널",
            font=ctk.CTkFont(family="맑은 고딕", size=16, weight="bold"),
            text_color="#ECF0F1",
        ).pack(anchor=tk.W, pady=(0, 8))

        button_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        button_frame.pack(fill=tk.X, padx=0, pady=10)

        # 제어 패널 버튼 공통 크기 및 비활성화 시 회색 스타일
        BTN_W, BTN_H = 200, 36
        DISABLED_FG = "#5D6D7E"
        DISABLED_TEXT = "#ECF0F1"

        self._control_btn_colors = {}

        load_btn = ctk.CTkButton(
            button_frame,
            text="🔄 새로고침",
            font=ctk.CTkFont(family="맑은 고딕", size=13, weight="bold"),
            fg_color="#27AE60",
            hover_color="#229954",
            text_color="#FFFFFF",
            width=BTN_W,
            height=BTN_H,
            cursor="hand2",
            command=self.load_google_sheet,
        )
        load_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.start_btn = ctk.CTkButton(
            button_frame,
            text="🖼️ 사건 조회 로드 실행\n(캡차 로드 실행)",
            font=ctk.CTkFont(family="맑은 고딕", size=13, weight="bold"),
            fg_color="#E67E22",
            hover_color="#D35400",
            text_color="#FFFFFF",
            width=BTN_W,
            height=BTN_H,
            cursor="hand2",
            command=self.start_batch_processing,
        )
        self._control_btn_colors[self.start_btn] = ("#E67E22", "#D35400", "#FFFFFF")
        self.start_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.complete_btn = ctk.CTkButton(
            button_frame,
            text="✔️ 캡차 입력 완료",
            font=ctk.CTkFont(family="맑은 고딕", size=13, weight="bold"),
            fg_color=DISABLED_FG,
            hover_color=DISABLED_FG,
            text_color=DISABLED_TEXT,
            width=BTN_W,
            height=BTN_H,
            cursor="hand2",
            command=self.start_processing_thread,
            state="disabled",
        )
        self._control_btn_colors[self.complete_btn] = ("#16A085", "#138D75", "#FFFFFF")
        self.complete_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.stop_btn = ctk.CTkButton(
            button_frame,
            text="⛔ 처리 중지",
            font=ctk.CTkFont(family="맑은 고딕", size=13, weight="bold"),
            fg_color=DISABLED_FG,
            hover_color=DISABLED_FG,
            text_color=DISABLED_TEXT,
            width=BTN_W,
            height=BTN_H,
            cursor="hand2",
            command=self.stop_batch_processing,
            state="disabled",
        )
        self._control_btn_colors[self.stop_btn] = ("#E74C3C", "#C0392B", "#FFFFFF")
        self.stop_btn.pack(side=tk.LEFT)

        return control_frame

    def _set_control_btn_state(self, btn, enabled):
        """제어 패널 버튼 활성/비활성 + 회색 스타일 적용. 비활성 시 글씨가 보이는 회색."""
        if enabled:
            colors = self._control_btn_colors.get(btn)
            if colors:
                fg, hover, text = colors
                btn.configure(
                    state="normal",
                    fg_color=fg,
                    hover_color=hover,
                    text_color=text,
                )
            else:
                btn.configure(state="normal")
        else:
            btn.configure(
                state="disabled",
                fg_color="#5D6D7E",
                hover_color="#5D6D7E",
                text_color="#ECF0F1",
            )

    def create_settings_panel(self, parent):
        """설정 패널 생성 (CustomTkinter)"""
        # 구분선: 제어 패널과 설정 패널 사이 (테마 색상 사용)
        sep = ctk.CTkFrame(
            parent, fg_color=self.get_theme_color("border"), height=2, corner_radius=0
        )
        sep.pack(fill=tk.X, padx=10, pady=(0, 4))
        sep.pack_propagate(False)

        settings_frame = ctk.CTkFrame(
            parent, fg_color=self.get_theme_color("bg_primary")
        )
        settings_frame.pack(fill=tk.X, padx=10, pady=5)
        ctk.CTkLabel(
            settings_frame,
            text="⚙️ 처리 설정",
            font=ctk.CTkFont(family="맑은 고딕", size=16, weight="bold"),
            text_color=self.get_theme_color("text_main"),
        ).pack(anchor=tk.W, pady=(0, 8))

        settings_inner = ctk.CTkFrame(
            settings_frame, fg_color=self.get_theme_color("bg_primary")
        )
        settings_inner.pack(fill=tk.X, padx=0, pady=8)

        ctk.CTkLabel(
            settings_inner,
            text="⚡ 병렬 처리 수:",
            font=ctk.CTkFont(family="맑은 고딕", size=13, weight="bold"),
            text_color=self.get_theme_color("text_main"),
        ).grid(row=0, column=0, sticky=tk.W, padx=(0, 10), pady=2)
        max_limit = getattr(config, "MAX_PARALLEL_LIMIT", 20)
        parallel_entry = ctk.CTkEntry(
            settings_inner,
            width=80,
            height=28,
            font=ctk.CTkFont(family="맑은 고딕", size=13),
        )
        parallel_entry.grid(row=0, column=1, sticky=tk.W, padx=(0, 25))
        parallel_entry.insert(0, str(self.max_parallel.get()))
        parallel_entry.bind(
            "<FocusOut>",
            lambda e: self._sync_spin(parallel_entry, self.max_parallel, 1, max_limit),
        )
        self._settings_parallel_entry = parallel_entry

        ctk.CTkLabel(
            settings_inner,
            text="🔄 캡차 재시도 횟수:",
            font=ctk.CTkFont(family="맑은 고딕", size=13, weight="bold"),
            text_color=self.get_theme_color("text_main"),
        ).grid(row=0, column=2, sticky=tk.W, padx=(0, 10), pady=2)
        retry_entry = ctk.CTkEntry(
            settings_inner,
            width=80,
            height=28,
            font=ctk.CTkFont(family="맑은 고딕", size=13),
        )
        retry_entry.grid(row=0, column=3, sticky=tk.W, padx=(0, 25))
        retry_entry.insert(0, str(self.max_retry.get()))
        retry_entry.bind(
            "<FocusOut>", lambda e: self._sync_spin(retry_entry, self.max_retry, 1, 10)
        )

        ctk.CTkLabel(
            settings_inner,
            text="⏱️ 재시도 간 대기시간(초):",
            font=ctk.CTkFont(family="맑은 고딕", size=13, weight="bold"),
            text_color=self.get_theme_color("text_main"),
        ).grid(row=0, column=4, sticky=tk.W, padx=(0, 10), pady=2)
        delay_entry = ctk.CTkEntry(
            settings_inner,
            width=80,
            height=28,
            font=ctk.CTkFont(family="맑은 고딕", size=13),
        )
        delay_entry.grid(row=0, column=5, sticky=tk.W, pady=2)
        delay_entry.insert(0, str(self.retry_delay.get()))
        delay_entry.bind(
            "<FocusOut>",
            lambda e: self._sync_spin(delay_entry, self.retry_delay, 1, 10),
        )

        # 테마 선택 (다크 / 라이트 / 시스템)
        theme_display = {
            "Dark": "다크(Dark)",
            "Light": "라이트(Light)",
            "System": "시스템(System)",
        }
        theme_options = ["다크(Dark)", "라이트(Light)", "시스템(System)"]
        current_display = theme_display.get(self._appearance_mode, "다크(Dark)")

        ctk.CTkLabel(
            settings_inner,
            text="🎨 테마:",
            font=ctk.CTkFont(family="맑은 고딕", size=13, weight="bold"),
            text_color=self.get_theme_color("text_main"),
        ).grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(12, 2))

        def on_theme_change(choice):
            mode = (
                "Dark"
                if choice == "다크(Dark)"
                else ("Light" if choice == "라이트(Light)" else "System")
            )
            self._apply_theme(mode)
            self._save_theme_setting(mode)
            if hasattr(self, "case_list") and self.case_list:
                self.update_case_list_ui()

        theme_var = ctk.StringVar(value=current_display)
        theme_menu = ctk.CTkOptionMenu(
            settings_inner,
            values=theme_options,
            variable=theme_var,
            width=140,
            command=on_theme_change,
        )
        theme_menu.grid(row=1, column=1, sticky=tk.W, padx=(0, 25), pady=(12, 2))
        self._theme_option_var = theme_var

        return settings_frame

    def _sync_spin(self, entry_widget, int_var, low, high):
        """Entry 값으로 IntVar 동기화 (범위 클램프)."""
        try:
            val = int(entry_widget.get().strip())
            val = max(low, min(high, val))
            int_var.set(val)
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, str(val))
        except (ValueError, tk.TclError):
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, str(int_var.get()))

    def create_case_list_panel(self, parent):
        """사건 목록 패널 생성 (CustomTkinter, Canvas 유지 for 가로 스크롤/리사이즈)"""
        # 구분선: 설정 패널과 사건 목록 사이 (테마 색상 사용)
        sep = ctk.CTkFrame(
            parent, fg_color=self.get_theme_color("border"), height=2, corner_radius=0
        )
        sep.pack(fill=tk.X, padx=10, pady=(0, 4))
        sep.pack_propagate(False)

        case_frame = ctk.CTkFrame(parent, fg_color="transparent")
        case_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 제목 + 열 순서 설정 버튼 + 검색창 한 줄
        title_row = ctk.CTkFrame(case_frame, fg_color="transparent")
        title_row.pack(anchor=tk.W, pady=(0, 4))
        ctk.CTkLabel(
            title_row,
            text="📋 사건 목록",
            font=ctk.CTkFont(family="맑은 고딕", size=16, weight="bold"),
            text_color=self.get_theme_color("text_main"),
        ).pack(side=tk.LEFT)
        settings_btn = ctk.CTkButton(
            title_row,
            text="⚙",
            font=ctk.CTkFont(size=16),
            width=36,
            height=28,
            fg_color="transparent",
            hover_color="#3D5A6C",
            cursor="hand2",
            command=self._open_column_order_dialog,
        )
        settings_btn.pack(side=tk.LEFT, padx=(8, 0))
        search_frame = ctk.CTkFrame(title_row, fg_color="transparent")
        search_frame.pack(side=tk.LEFT, padx=(16, 0))
        self.search_entry = ctk.CTkEntry(
            search_frame,
            width=200,
            height=28,
            font=ctk.CTkFont(family="맑은 고딕", size=12),
            placeholder_text="검색...",
        )
        self.search_entry.pack(side=tk.LEFT, padx=(0, 6))
        self.search_entry.bind("<Return>", lambda e: self.perform_search())
        search_btn = ctk.CTkButton(
            search_frame,
            text="찾기",
            width=60,
            height=28,
            font=ctk.CTkFont(family="맑은 고딕", size=12),
            cursor="hand2",
            command=self.perform_search,
        )
        search_btn.pack(side=tk.LEFT)

        main_container = ctk.CTkFrame(case_frame, fg_color="transparent")
        main_container.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        # 가로 스크롤 시 헤더/리스트 동기화
        def _sync_xview(first, last):
            self.header_canvas.xview_moveto(first)
            self.case_canvas.xview_moveto(first)

        self.header_canvas = tk.Canvas(
            main_container,
            bg="#2B2B2B",
            height=40,
            highlightthickness=0,
            bd=0,
        )
        self.header_canvas.pack(fill=tk.X)

        self.case_canvas = tk.Canvas(
            main_container, bg="#2B2B2B", highlightthickness=0, bd=0
        )
        v_scrollbar = ttk.Scrollbar(
            main_container, orient="vertical", command=self.case_canvas.yview
        )
        h_scrollbar = ttk.Scrollbar(
            main_container, orient="horizontal", command=_sync_xview
        )

        self.header_container = ctk.CTkFrame(
            self.header_canvas, fg_color="#34495E", height=40, width=400
        )
        self.header_container.pack_propagate(False)
        self.header_canvas.create_window(
            (0, 0), window=self.header_container, anchor="nw"
        )
        self.header_canvas.configure(xscrollcommand=h_scrollbar.set)
        self.header_canvas.configure(scrollregion=(0, 0, 400, 40))

        self.case_list_frame = ctk.CTkFrame(
            self.case_canvas,
            fg_color="#2B2B2B",
            width=400,
            corner_radius=0,
            border_width=0,
        )
        # pack_propagate(False) 사용 안 함 → 세로로 자식(행)만큼 늘어나 전부 표시
        self.case_canvas.create_window(
            (0, 0), window=self.case_list_frame, anchor="nw"
        )

        def _update_scroll_region(_=None):
            self.case_canvas.update_idletasks()
            self.case_canvas.configure(scrollregion=self.case_canvas.bbox("all"))

        self.case_list_frame.bind("<Configure>", _update_scroll_region)

        def _on_canvas_configure(_=None):
            _update_scroll_region()
            if hasattr(self, "col_order") and len(self.col_order) > 0:
                self.apply_column_width(len(self.col_order) - 1)

        self.case_canvas.bind("<Configure>", _on_canvas_configure)
        self.case_canvas.configure(yscrollcommand=v_scrollbar.set)
        self.case_canvas.configure(xscrollcommand=h_scrollbar.set)

        # 마우스 휠: 목록 영역 세로 스크롤. 하위 위젯(행, 텍스트박스 등)에도 전파되도록 나중에 _bind_mousewheel_to_case_list()에서 일괄 바인딩
        self._case_list_mousewheel_handler = lambda e: self.case_canvas.yview_scroll(
            int(-1 * (e.delta / 120)), "units"
        )
        self.case_canvas.bind("<MouseWheel>", self._case_list_mousewheel_handler)
        self.case_list_frame.bind("<MouseWheel>", self._case_list_mousewheel_handler)

        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X, padx=0, pady=0)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=0, pady=0)
        self.case_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=0, pady=0)

        # Ctrl+F: 찾기 다이얼로그
        self.root.bind("<Control-f>", self._open_find_dialog)

        return case_frame

    _FIND_HIGHLIGHT_TAG = "find_highlight"

    def _clear_find_highlights(self):
        if not hasattr(self, "case_info_text_widgets"):
            return
        for widgets in self.case_info_text_widgets.values():
            for w in widgets:
                if w.winfo_exists():
                    try:
                        w.tag_remove(self._FIND_HIGHLIGHT_TAG, "1.0", tk.END)
                    except (tk.TclError, AttributeError):
                        pass

    def _apply_find_highlight(self, row_index, q):
        if not q or not hasattr(self, "case_info_text_widgets"):
            return
        widgets = self.case_info_text_widgets.get(row_index, [])
        q_lower = q.lower()
        for w in widgets:
            if not w.winfo_exists():
                continue
            try:
                w.configure(state="normal")
                content = w.get("1.0", tk.END).rstrip("\n")
                content_lower = content.lower()
                pos = 0
                while True:
                    idx = content_lower.find(q_lower, pos)
                    if idx < 0:
                        break
                    w.tag_add(
                        self._FIND_HIGHLIGHT_TAG,
                        f"1.{idx}",
                        f"1.{idx + len(q)}",
                    )
                    pos = idx + 1
                w.tag_config(
                    self._FIND_HIGHLIGHT_TAG,
                    background="#FFF176",
                    foreground="#000000",
                )
                w.configure(state="disabled")
            except (tk.TclError, AttributeError):
                pass

    def _scroll_to_row_and_highlight(self, row_index, query):
        if not hasattr(self, "case_frames") or row_index not in self.case_frames:
            return
        row_frame = self.case_frames[row_index]
        row_container = row_frame.master
        self.case_canvas.update_idletasks()
        bbox = self.case_canvas.bbox("all")
        if not bbox:
            return
        total_h = bbox[3] - bbox[1]
        y_in_list = row_container.winfo_y()
        y_in_canvas = y_in_list
        fraction = max(0.0, min(1.0, (y_in_canvas - 20) / total_h))
        self.case_canvas.yview_moveto(fraction)
        self._clear_find_highlights()
        self._apply_find_highlight(row_index, query)
        orig_fg = (
            self.get_theme_color("row_odd")
            if row_index % 2 == 0
            else self.get_theme_color("row_even")
        )
        try:
            row_frame.configure(fg_color="#B3D9FF")
            for c in row_frame.winfo_children():
                try:
                    c.configure(fg_color="#B3D9FF")
                except (tk.TclError, AttributeError):
                    try:
                        c.config(bg="#B3D9FF")
                    except Exception:
                        pass
        except Exception:
            pass

        def restore():
            try:
                row_frame.configure(fg_color=orig_fg)
                for c in row_frame.winfo_children():
                    try:
                        c.configure(fg_color=orig_fg)
                    except (tk.TclError, AttributeError):
                        try:
                            c.config(bg=orig_fg)
                        except Exception:
                            pass
            except Exception:
                pass

        self.root.after(800, restore)

    def _find_match_indices(self, query):
        if not query or not hasattr(self, "case_list"):
            return []

        def case_search_text(case):
            return " ".join(
                [
                    str(case.get("법원", "") or ""),
                    str(case.get("사건번호", "") or ""),
                    str(case.get("피고", "") or ""),
                    str(case.get("사건명", "") or ""),
                    str(case.get("비고", "") or ""),
                ]
            ).lower()

        q = query.strip().lower()
        return [i for i, c in enumerate(self.case_list) if q in case_search_text(c)]

    def perform_search(self, query=None):
        """상단 검색창 또는 팝업에서 호출. query가 None이면 self.search_entry에서 가져옴."""
        if query is None and hasattr(self, "search_entry") and self.search_entry.winfo_exists():
            query = self.search_entry.get().strip()
        if not query:
            return
        match_indices = self._find_match_indices(query)
        if not match_indices:
            messagebox.showinfo("찾기", "검색어와 일치하는 항목이 없습니다.")
            return
        self._scroll_to_row_and_highlight(match_indices[0], query)

    def _bind_mousewheel_recursive(self, widget, handler):
        """위젯과 그 자손 모두에 마우스 휠 핸들러를 바인딩 (사건 목록 내 어디서나 휠 스크롤 가능)."""
        try:
            widget.bind("<MouseWheel>", handler)
        except tk.TclError:
            pass
        for child in widget.winfo_children():
            self._bind_mousewheel_recursive(child, handler)

    def _bind_mousewheel_to_case_list(self):
        """사건 목록 캔버스/내부 프레임 및 모든 하위 위젯에 마우스 휠 스크롤 바인딩."""
        if not hasattr(self, "_case_list_mousewheel_handler") or not hasattr(
            self, "case_list_frame"
        ):
            return
        if not self.case_list_frame.winfo_exists():
            return
        self._bind_mousewheel_recursive(
            self.case_list_frame, self._case_list_mousewheel_handler
        )

    def _open_column_order_dialog(self):
        """열 순서 설정 팝업. 위로/아래로로 순서 변경 후 적용 시 저장 및 목록 갱신."""
        if (
            getattr(self, "_column_order_dialog", None) is not None
            and self._column_order_dialog.winfo_exists()
        ):
            self._column_order_dialog.focus_set()
            return

        dlg = ctk.CTkToplevel(self.root)
        dlg.title("사건 목록 열 순서")
        dlg.geometry("320x380")
        dlg.transient(self.root)
        dlg.resizable(False, False)
        self._column_order_dialog = dlg

        frm = ctk.CTkFrame(dlg, fg_color="transparent")
        frm.pack(fill=tk.BOTH, expand=True, padx=14, pady=14)

        # 현재 순서 복사 (다이얼로그 내에서만 변경)
        order = list(self.col_order)

        # 버튼 행을 먼저 하단에 고정 (expand=True 리스트가 공간을 다 차지해 버튼이 가려지는 것 방지)
        sep_line = ctk.CTkFrame(
            frm, fg_color=self.get_theme_color("border"), height=2, corner_radius=0
        )
        sep_line.pack(side=tk.BOTTOM, fill=tk.X, pady=(12, 0))
        sep_line.pack_propagate(False)

        btn_row = ctk.CTkFrame(frm, fg_color="transparent")
        btn_row.pack(side=tk.BOTTOM, fill=tk.X, pady=(0, 4))
        # 그리드로 배치해 위로/아래로·취소/적용 간격을 통일하고, 가운데 여백으로 좌우 균형 유지
        btn_row.grid_columnconfigure(2, weight=1)

        def move_up():
            sel = listbox.curselection()
            if not sel or sel[0] == 0:
                return
            i = sel[0]
            order[i], order[i - 1] = order[i - 1], order[i]
            refresh_list()
            listbox.selection_set(i - 1)

        def move_down():
            sel = listbox.curselection()
            if not sel or sel[0] >= len(order) - 1:
                return
            i = sel[0]
            order[i], order[i + 1] = order[i + 1], order[i]
            refresh_list()
            listbox.selection_set(i + 1)

        def apply_and_close():
            self.col_order[:] = order
            self._save_column_order()
            if hasattr(self, "case_list") and self.case_list:
                self.update_case_list_ui()
            if self._column_order_dialog and self._column_order_dialog.winfo_exists():
                self._column_order_dialog.destroy()
            self._column_order_dialog = None

        BTN_PAD = 8  # 버튼 간 동일 간격 (px)
        ctk.CTkButton(
            btn_row,
            text="위로",
            width=70,
            height=36,
            text_color="#FFFFFF",
            command=move_up,
        ).grid(row=0, column=0, padx=(0, BTN_PAD), sticky="w")
        ctk.CTkButton(
            btn_row,
            text="아래로",
            width=70,
            height=36,
            text_color="#FFFFFF",
            command=move_down,
        ).grid(row=0, column=1, padx=(0, 0), sticky="w")
        # column 2: 가운데 빈 공간 (weight=1)
        ctk.CTkButton(
            btn_row,
            text="취소",
            width=70,
            height=36,
            text_color="#FFFFFF",
            command=dlg.destroy,
        ).grid(row=0, column=3, padx=(BTN_PAD * 2, BTN_PAD), sticky="e")
        ctk.CTkButton(
            btn_row,
            text="적용",
            width=70,
            height=36,
            text_color="#FFFFFF",
            command=apply_and_close,
        ).grid(row=0, column=4, padx=(0, 0), sticky="e")

        # 제목 라벨 (상단)
        ctk.CTkLabel(
            frm,
            text="표시 순서 (위에서 아래가 왼쪽에서 오른쪽)",
            font=ctk.CTkFont(family="맑은 고딕", size=13),
        ).pack(anchor=tk.W, pady=(0, 6))

        # 리스트 영역 (가운데, 남는 공간만 사용해 버튼이 항상 보이도록)
        list_frame = ctk.CTkFrame(frm, fg_color=("#2B2B2B", "#2B2B2B"))
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 4))

        listbox = tk.Listbox(
            list_frame,
            font=("맑은 고딕", 13),
            selectbackground=self.get_theme_color("accent"),
            selectforeground="white",
            bg="#2B2B2B",
            fg="white",
            relief=tk.FLAT,
            highlightthickness=0,
            height=12,
        )
        listbox.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        def refresh_list():
            listbox.delete(0, tk.END)
            for internal_idx in order:
                listbox.insert(tk.END, COL_NAMES[internal_idx])

        refresh_list()
        if order:
            listbox.selection_set(0)

        dlg.protocol("WM_DELETE_WINDOW", dlg.destroy)

    def _open_find_dialog(self, event=None):
        """Ctrl+F 시 찾기 다이얼로그. 검색어 형광펜 하이라이트 (CTkTextbox tag)."""
        if (
            getattr(self, "_find_dialog", None) is not None
            and self._find_dialog.winfo_exists()
        ):
            self._find_dialog.focus_set()
            return "break"

        dlg = ctk.CTkToplevel(self.root)
        dlg.title("찾기")
        dlg.geometry("400x140")
        dlg.transient(self.root)
        dlg.resizable(False, False)
        self._find_dialog = dlg

        frm = ctk.CTkFrame(dlg, fg_color="transparent")
        frm.pack(fill=tk.BOTH, expand=True, padx=14, pady=14)

        ctk.CTkLabel(frm, text="검색어:").pack(anchor=tk.W)
        entry_var = tk.StringVar()
        entry = ctk.CTkEntry(frm, textvariable=entry_var, width=320, height=32)
        entry.pack(fill=tk.X, pady=(0, 10))
        entry.focus_set()

        match_indices = []
        current_index = [0]

        def find_matches():
            q = entry_var.get().strip()
            match_indices[:] = self._find_match_indices(q)

        def on_find():
            self._clear_find_highlights()
            find_matches()
            current_index[0] = 0
            if not match_indices:
                messagebox.showinfo(
                    "찾기", "검색어와 일치하는 항목이 없습니다.", parent=dlg
                )
                return
            self._scroll_to_row_and_highlight(
                match_indices[0], entry_var.get().strip()
            )

        def on_next():
            self._clear_find_highlights()
            find_matches()
            if not match_indices:
                messagebox.showinfo(
                    "찾기", "검색어와 일치하는 항목이 없습니다.", parent=dlg
                )
                return
            current_index[0] = (current_index[0] + 1) % len(match_indices)
            self._scroll_to_row_and_highlight(
                match_indices[current_index[0]], entry_var.get().strip()
            )

        btn_frm = ctk.CTkFrame(frm, fg_color="transparent")
        btn_frm.pack(fill=tk.X, pady=(4, 0))
        ctk.CTkButton(btn_frm, text="찾기", command=on_find, width=100).pack(
            side=tk.LEFT, padx=(0, 8)
        )
        ctk.CTkButton(btn_frm, text="다음 찾기", command=on_next, width=100).pack(
            side=tk.LEFT
        )

        def on_closing():
            self._clear_find_highlights()
            self._find_dialog = None
            dlg.destroy()

        dlg.protocol("WM_DELETE_WINDOW", on_closing)

        return "break"

    def create_progress_panel(self, parent):
        """진행상황 패널 생성 (CustomTkinter)"""
        progress_frame = ctk.CTkFrame(
            parent, fg_color=self.get_theme_color("bg_primary")
        )
        progress_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        ctk.CTkLabel(
            progress_frame,
            text="📊 진행상황",
            font=ctk.CTkFont(family="맑은 고딕", size=16, weight="bold"),
            text_color=self.get_theme_color("text_main"),
        ).pack(anchor=tk.W, pady=(0, 8))

        self.progress_var = tk.DoubleVar()
        # width를 제거하여 부모 너비에 맞춰 유동적으로 조절되도록 함
        self.progress_bar = ctk.CTkProgressBar(progress_frame, height=16)
        self.progress_bar.pack(fill=tk.X, padx=0, pady=10)
        self.progress_bar.set(0)

        # 진행률 바와 로그 영역 사이 구분선 (테마 색상 사용)
        sep = ctk.CTkFrame(
            progress_frame,
            fg_color=self.get_theme_color("border"),
            height=2,
            corner_radius=0,
        )
        sep.pack(fill=tk.X, pady=(0, 8))
        sep.pack_propagate(False)

        self.status_text = ctk.CTkTextbox(
            progress_frame,
            font=ctk.CTkFont(family="맑은 고딕", size=12),
            fg_color="#34495E",
            text_color="#ECF0F1",
            wrap=tk.WORD,
            height=300,
            width=100, # 초기 너비 설정 (fill=BOTH에 의해 조절됨)
        )
        self.status_text.pack(fill=tk.BOTH, expand=True, padx=0, pady=(0, 10))

        return progress_frame

    def reset_internal_data(self):
        """
        새로고침 시 이전 작업의 잔재(이미지, 입력값 등)를 비우는 메서드.
        status_text(로그)는 건드리지 않아 로그는 유지된다.
        """
        for key in (
            "case_checkboxes",
            "case_inputs",
            "case_entries",
            "case_status",
            "case_images",
            "case_image_photos",
            "case_frames",
            "case_update_labels",
            "case_update_date_labels",
            "case_start_times",
            "case_info_text_widgets",
            "case_cell_frames",
            "case_separators",
            "browser_ws_urls",
            "browser_processes",
        ):
            setattr(self, key, {})

    def sort_case_list(self):
        """현재 정렬 기준(sort_column_index, sort_reverse)으로 case_list를 정렬한다."""
        if not self.case_list:
            return
        history = self.load_update_history()
        search_log = self.load_search_log()

        def sort_key(case):
            cn = case.get("사건번호", "")
            if self.sort_column_index == 1:
                return f"{case.get('법원', '')} {case.get('사건번호', '')}".strip()
            if self.sort_column_index == 2:
                return f"{case.get('피고', '')} {case.get('사건명', '')}".strip()
            if self.sort_column_index == 3:
                return case.get("비고", "")
            if self.sort_column_index == 7:
                # 기록(쿠키): search_log 기준, 있으면 1 없으면 0
                return 1 if cn in search_log else 0
            if self.sort_column_index == 8:
                # 최근 업데이트: 날짜 문자열, 없으면 과거로
                data = history.get(cn, {})
                if isinstance(data, dict):
                    return data.get("last_update", "1900-01-01 00:00:00")
                return data if isinstance(data, str) else "1900-01-01 00:00:00"
            return ""

        self.case_list.sort(key=sort_key, reverse=self.sort_reverse)

    def on_header_click(self, col_idx):
        """헤더 클릭 시 정렬 기준 변경 후 목록 재정렬 및 UI 갱신."""
        sortable = (1, 2, 3, 7, 8)
        if col_idx not in sortable:
            return
        if self.sort_column_index == col_idx:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column_index = col_idx
            self.sort_reverse = False
        self.sort_case_list()
        self.update_case_list_ui()

    def load_google_sheet(self):
        """구글 시트에서 사건 목록 로드"""
        # 새로고침 시 '사건 조회 로드 실행' 버튼을 원래 색/텍스트/활성 상태로 복구
        self.start_btn.configure(text="🖼️ 사건 조회 로드 실행\n(캡차 로드 실행)")
        self._set_control_btn_state(self.start_btn, True)

        self.reset_internal_data()

        # 쿠키 폴더가 삭제된 경우 검색 기록(search_log.json)도 자동 초기화 (표시 불일치 방지)
        cookie_dir = getattr(config, "COOKIE_DATA_DIR", "cookie_data_for_save")
        search_log_path = getattr(config, "SEARCH_LOG_FILE", "search_log.json")
        if not os.path.isdir(cookie_dir) and os.path.isfile(search_log_path):
            try:
                os.remove(search_log_path)
                self.log_message("쿠키 데이터가 삭제되어 검색 기록을 초기화했습니다.")
            except Exception as e:
                self.log_message(f"⚠️ 검색 기록 초기화 실패: {e}")

        try:
            self.log_message("구글 시트 연결 중...")
            # services/google_sheets.py의 함수 사용
            google_data, spreadsheet = load_google_sheet_data()

            if not google_data:
                messagebox.showerror("오류", "구글 시트 데이터를 로드할 수 없습니다.")
                return

            self.case_list = google_data
            self.sort_case_list()

            # 스마트 병렬 수: 사건 수의 절반으로 자동 설정 (최대 config.MAX_PARALLEL_LIMIT)
            max_limit = getattr(config, "MAX_PARALLEL_LIMIT", 20)
            n_cases = len(self.case_list)
            smart_parallel = max(1, min(n_cases // 2, max_limit))
            self.max_parallel.set(smart_parallel)
            if (
                hasattr(self, "_settings_parallel_entry")
                and self._settings_parallel_entry.winfo_exists()
            ):
                self._settings_parallel_entry.delete(0, tk.END)
                self._settings_parallel_entry.insert(0, str(smart_parallel))
            if smart_parallel > 10:
                self.log_message(
                    "⚠️ 고성능 모드: 인스턴스 폴더가 10개 이상 사용됩니다. 디스크/RAM 사용량이 늘어날 수 있습니다."
                )

            self.log_message(
                f"✅ {len(google_data)}개 사건 로드 완료 (병렬 처리: {smart_parallel}개)"
            )

            # 사건 목록 UI 업데이트
            self.update_case_list_ui()

        except Exception as e:
            self.log_message(f"❌ 구글 시트 로드 실패: {e}")
            messagebox.showerror("오류", f"구글 시트 로드 실패: {e}")

    def _display_width_up_to(self, display_idx):
        """표시 순서상 display_idx(포함)까지의 누적 너비. 리사이즈 가이드라인 위치 계산용."""
        return sum(self.col_widths[self.col_order[i]] for i in range(display_idx + 1))

    def _get_effective_widths(self):
        """캔버스 너비를 반영한 전체 너비와 마지막 열(비고) 여분. (effective_total, extra_last) 반환."""
        if not hasattr(self, "col_widths") or not hasattr(self, "col_order"):
            return sum(getattr(self, "col_widths", [400])), 0
        total = sum(self.col_widths)
        if not hasattr(self, "case_canvas") or not self.case_canvas.winfo_exists():
            return total, 0
        self.case_canvas.update_idletasks()
        canvas_w = self.case_canvas.winfo_width()
        extra = max(0, canvas_w - total)
        return total + extra, extra

    def create_list_header(self):
        """사건 목록 헤더 생성 (col_order 순서대로 표시)"""
        # 기존 헤더 제거
        for widget in self.header_container.winfo_children():
            widget.destroy()

        self.header_cell_frames = []

        # 정렬 가능한 열 = 내부 인덱스 1,2,3,7,8 (법원/사건번호, 피고/사건명, 비고, 기록, 최근 업데이트)
        sortable_internal = (1, 2, 3, 7, 8)

        header_frame = ctk.CTkFrame(self.header_container, fg_color="#34495E")
        header_frame.pack(fill=tk.BOTH, expand=True)

        extra_last = getattr(self, "_extra_width_last_col", 0)
        last_internal = self.col_order[-1] if self.col_order else None
        for disp_idx, internal_idx in enumerate(self.col_order):
            name = COL_NAMES[internal_idx]
            width = self.col_widths[internal_idx] + (
                extra_last if internal_idx == last_internal else 0
            )
            # 헤더 셀: tk.Frame으로 변경 (데이터 행과 동일 구조)
            cell = tk.Frame(
                header_frame,
                bg="#34495E",
                width=width,
                height=40,
                bd=0,
                highlightthickness=0,
            )
            cell.pack(side=tk.LEFT)
            cell.pack_propagate(False)
            self.header_cell_frames.append(cell)

            # 선택 열: 리사이즈 핸들을 먼저 pack해 우측에 두고, 체크박스는 셀 정중앙에 place
            if internal_idx == 0:
                handle = tk.Frame(cell, bg="#34495E", width=10, height=40)
                handle.pack(side=tk.RIGHT, fill=tk.Y)
                handle.pack_propagate(False)
                line = tk.Frame(handle, bg="white", width=1, height=40)
                line.pack(side=tk.RIGHT, fill=tk.Y, padx=1)
                handle.config(cursor="sb_h_double_arrow")
                handle.bind(
                    "<ButtonPress-1>",
                    lambda e, d=disp_idx: self._on_resize_press(d, e),
                )
                handle.bind(
                    "<B1-Motion>",
                    lambda e, d=disp_idx: self._on_resize_motion(d, e),
                )
                handle.bind("<ButtonRelease-1>", lambda e: self._on_resize_release(e))
                header_cb = ctk.CTkCheckBox(
                    cell,
                    text="",
                    variable=self.header_select_all_var,
                    font=ctk.CTkFont(family="맑은 고딕", size=12),
                    width=24,
                    fg_color="#3D5A6C",
                    text_color=self.get_theme_color("text_header"),
                    command=self._on_header_select_toggle,
                )
                header_cb.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
            elif internal_idx in sortable_internal:
                arrow = (
                    " ▼"
                    if (self.sort_column_index == internal_idx and self.sort_reverse)
                    else " ▲"
                )
                if self.sort_column_index != internal_idx:
                    arrow = ""
                display_text = name + arrow
                btn = ctk.CTkButton(
                    cell,
                    text=display_text,
                    font=ctk.CTkFont(family="맑은 고딕", size=12, weight="bold"),
                    fg_color="transparent",
                    hover_color="#3D5A6C",
                    text_color=self.get_theme_color("text_header"),
                    anchor=tk.CENTER,
                    cursor="hand2",
                    command=lambda c=internal_idx: self.on_header_click(c),
                )
                btn.pack(fill=tk.BOTH, expand=True)
            else:
                label = ctk.CTkLabel(
                    cell,
                    text=name,
                    font=ctk.CTkFont(family="맑은 고딕", size=12, weight="bold"),
                    text_color=self.get_theme_color("text_header"),
                )
                label.pack(fill=tk.BOTH, expand=True)

            # 리사이즈 핸들 (선택 열은 위에서 이미 생성)
            if internal_idx != 0:
                handle = tk.Frame(cell, bg="#34495E", width=10, height=40)
                handle.pack(side=tk.RIGHT, fill=tk.Y)
                handle.pack_propagate(False)
                line = tk.Frame(handle, bg="white", width=1, height=40)
                line.pack(side=tk.RIGHT, fill=tk.Y, padx=1)
                handle.config(cursor="sb_h_double_arrow")
                handle.bind(
                    "<ButtonPress-1>",
                    lambda e, d=disp_idx: self._on_resize_press(d, e),
                )
                handle.bind(
                    "<B1-Motion>",
                    lambda e, d=disp_idx: self._on_resize_motion(d, e),
                )
                handle.bind("<ButtonRelease-1>", lambda e: self._on_resize_release(e))


    def _on_resize_press(self, display_idx, event):
        """display_idx: 표시 순서상 열 인덱스 (0~9). 내부 열 인덱스는 col_order[display_idx]."""
        self._resize_col = display_idx
        internal_idx = self.col_order[display_idx]
        self._resize_start_x = event.x_root
        self._resize_start_width = self.col_widths[internal_idx]
        self._resize_current_width = self.col_widths[internal_idx]
        if hasattr(self, "case_list_frame") and self.case_list_frame.winfo_exists():
            if self.resize_guide_line and self.resize_guide_line.winfo_exists():
                self.resize_guide_line.destroy()
            x_pos = self._display_width_up_to(display_idx)
            self.resize_guide_line = tk.Frame(
                self.case_list_frame, width=1, bg="#2C3E50", height=10000
            )
            self.resize_guide_line.place(x=x_pos, y=0, anchor=tk.NW)

    def _on_resize_motion(self, display_idx, event):
        if self._resize_col is None:
            return
        delta = event.x_root - self._resize_start_x
        new_w = max(30, min(500, self._resize_start_width + delta))
        self._resize_current_width = new_w
        if self.resize_guide_line and self.resize_guide_line.winfo_exists():
            x_pos = (
                sum(self.col_widths[self.col_order[i]] for i in range(display_idx))
                + new_w
            )
            self.resize_guide_line.place_configure(x=x_pos)

    def _on_resize_release(self, event):
        if self._resize_col is not None:
            display_idx = self._resize_col
            internal_idx = self.col_order[display_idx]
            self._resize_col = None
            self._resize_start_x = None
            self._resize_start_width = None
            if self.resize_guide_line and self.resize_guide_line.winfo_exists():
                self.resize_guide_line.destroy()
                self.resize_guide_line = None
            if self._resize_current_width is not None:
                self.col_widths[internal_idx] = int(self._resize_current_width)
                self._resize_current_width = None
            self._save_column_widths()
            self.apply_column_width(display_idx)

    def apply_column_width(self, display_idx):
        """리사이즈 후 해당 표시 열 너비만 적용 (display_idx = 표시 순서상 인덱스). 비고 열은 캔버스 여분 반영."""
        if not hasattr(self, "col_order") or display_idx >= len(self.col_order):
            return
        effective_total, extra_last = self._get_effective_widths()
        self._extra_width_last_col = extra_last
        last_internal = self.col_order[-1]
        last_disp_idx = len(self.col_order) - 1
        internal_idx = self.col_order[display_idx]
        w = self.col_widths[internal_idx] + (
            extra_last if internal_idx == last_internal else 0
        )
        if hasattr(self, "header_cell_frames") and display_idx < len(
            self.header_cell_frames
        ):
            self.header_cell_frames[display_idx].configure(width=w)
        if hasattr(self, "case_cell_frames"):
            for row_cells in self.case_cell_frames.values():
                if display_idx < len(row_cells):
                    row_cells[display_idx].config(width=w)
        # 마지막 열(비고)도 여분 반영해 한 번 더 적용 (다른 열 리사이즈 시 캔버스 너비가 바뀐 경우 대비)
        w_last = self.col_widths[last_internal] + extra_last
        if last_disp_idx != display_idx and hasattr(
            self, "header_cell_frames"
        ) and last_disp_idx < len(self.header_cell_frames):
            self.header_cell_frames[last_disp_idx].configure(width=w_last)
        if hasattr(self, "case_cell_frames"):
            for row_cells in self.case_cell_frames.values():
                if last_disp_idx < len(row_cells):
                    row_cells[last_disp_idx].config(width=w_last)
        if hasattr(self, "header_container") and self.header_container.winfo_exists():
            self.header_container.configure(width=effective_total)
        if hasattr(self, "header_canvas") and self.header_canvas.winfo_exists():
            self.header_canvas.configure(
                scrollregion=(0, 0, effective_total, 40)
            )
        if hasattr(self, "case_list_frame") and self.case_list_frame.winfo_exists():
            self.case_list_frame.configure(width=effective_total)
        if hasattr(self, "case_frames"):
            for case_frame in self.case_frames.values():
                if case_frame.winfo_exists():
                    case_frame.configure(width=effective_total)
        if hasattr(self, "case_separators"):
            for sep in self.case_separators.values():
                if sep.winfo_exists():
                    sep.config(width=effective_total)

    def create_case_row(self, parent, case, index, total_width, initial_status=None):
        """
        단일 사건 행 위젯 생성. col_order 순서대로 열을 배치한다.
        """
        bg_color = (
            self.get_theme_color("row_odd")
            if index % 2 == 0
            else self.get_theme_color("row_even")
        )
        row_container = ctk.CTkFrame(parent, fg_color="transparent")
        row_container.pack(fill=tk.X, pady=0, padx=0)

        case_frame = ctk.CTkFrame(
            row_container,
            fg_color=bg_color,
            height=60,
            width=total_width,
            corner_radius=0,
        )
        case_frame.pack(fill=tk.X)
        case_frame.pack_propagate(False)

        separator = tk.Frame(
            row_container,
            bg=self.get_theme_color("border"),
            height=1,
            width=total_width,
            bd=0,
            highlightthickness=0,
        )
        separator.pack(fill=tk.X)
        separator.pack_propagate(False)
        self.case_separators[index] = separator

        components = {}
        # 내부 인덱스(0~9)별 셀 프레임: tk.Frame으로 고정 너비/정렬 및 성능 확보
        # 마지막 열(비고)에는 캔버스 여분 너비를 더해 우측 끝까지 채움
        extra_last = getattr(self, "_extra_width_last_col", 0)
        last_internal = self.col_order[-1] if self.col_order else None

        def _cell_width(internal_idx):
            return self.col_widths[internal_idx] + (
                extra_last if internal_idx == last_internal else 0
            )

        frames_by_internal = [None] * len(COL_NAMES)

        # 0: 선택
        var = tk.BooleanVar()
        f0 = tk.Frame(
            case_frame,
            bg=bg_color,
            width=_cell_width(0),
            height=60,
            bd=0,
            highlightthickness=0,
        )
        f0.pack_propagate(False)
        frames_by_internal[0] = f0
        ctk.CTkCheckBox(
            f0,
            variable=var,
            text="",
            fg_color=bg_color,
            width=24,
            command=lambda idx=index: self.on_checkbox_change(idx),
        ).place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        components["checkbox_var"] = var

        # 1,2,3: 법원/사건번호, 피고/사건명, 비고
        info_parts = [
            f"{case.get('법원', '')} {case.get('사건번호', '')}".strip(),
            f"{case.get('피고', '')} {case.get('사건명', '')}".strip(),
            str(case.get("비고", "") or ""),
        ]
        for i, text in enumerate(info_parts, start=1):
            fi = tk.Frame(
                case_frame,
                bg=bg_color,
                width=_cell_width(i),
                height=60,
                bd=0,
                highlightthickness=0,
            )
            fi.pack_propagate(False)
            frames_by_internal[i] = fi
            tb = ctk.CTkTextbox(
                fi,
                font=ctk.CTkFont(family="맑은 고딕", size=13),
                fg_color=bg_color,
                text_color=self.get_theme_color("text_main"),
                height=36,
                activate_scrollbars=False,
                wrap=tk.NONE,
                border_width=0,
            )
            tb.pack(fill=tk.X, expand=True, padx=6, pady=12)
            tb.insert("1.0", text)
            tb.configure(state="disabled")
            components[f"label_info_{i}"] = tb

        # 4: 캡차 이미지
        f4 = tk.Frame(
            case_frame,
            bg=bg_color,
            width=_cell_width(4),
            height=60,
            bd=0,
            highlightthickness=0,
        )
        f4.pack_propagate(False)
        frames_by_internal[4] = f4
        il = tk.Label(
            f4,
            text="대기중",
            font=self.get_theme_color("font_small"),
            fg=self.get_theme_color("text_sub"),
            bg=self.get_theme_color("bg_primary"),
            relief=tk.FLAT,
        )
        il.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        components["image_label"] = il

        # 5: 캡차 입력
        f5 = tk.Frame(
            case_frame,
            bg=bg_color,
            width=_cell_width(5),
            height=60,
            bd=0,
            highlightthickness=0,
        )
        f5.pack_propagate(False)
        frames_by_internal[5] = f5
        captcha_var = tk.StringVar()
        captcha_entry = ctk.CTkEntry(
            f5,
            textvariable=captcha_var,
            font=ctk.CTkFont(family="맑은 고딕", size=14, weight="bold"),
            justify=tk.CENTER,
            width=70,
            height=28,
        )
        captcha_entry.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        captcha_entry.bind(
            "<KeyRelease>", lambda e, idx=index: self._validate_captcha_entry(idx)
        )
        try:
            captcha_entry.bind(
                "<Return>", lambda e, idx=index: self.on_captcha_enter(idx)
            )
        except Exception:
            pass
        components["captcha_var"] = captcha_var
        components["captcha_entry"] = captcha_entry

        # 6: 상태
        f6 = tk.Frame(
            case_frame,
            bg=bg_color,
            width=_cell_width(6),
            height=60,
            bd=0,
            highlightthickness=0,
        )
        f6.pack_propagate(False)
        frames_by_internal[6] = f6
        if initial_status and isinstance(initial_status, dict):
            st = initial_status.get("status", "대기")
            em = initial_status.get("emoji", "⏸️")
            status_text = f"{em} {st}" if em else st
            status_fg = initial_status.get("color", self.get_theme_color("text_sub"))
        else:
            status_text, status_fg = "⏸️ 대기", self.get_theme_color("text_sub")
        sl = ctk.CTkLabel(
            f6,
            text=status_text,
            font=ctk.CTkFont(family="맑은 고딕", size=13),
            text_color=status_fg,
        )
        sl.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        components["status_label"] = sl

        # 7: 기록
        f7 = tk.Frame(
            case_frame,
            bg=bg_color,
            width=_cell_width(7),
            height=60,
            bd=0,
            highlightthickness=0,
        )
        f7.pack_propagate(False)
        frames_by_internal[7] = f7
        cn = case.get("사건번호", "")
        search_log = self.load_search_log()
        if cn in search_log:
            record_text, record_fg = "🍪 검색함", self.get_theme_color("success")
        else:
            record_text, record_fg = "-", self.get_theme_color("text_sub")
        rl = ctk.CTkLabel(
            f7,
            text=record_text,
            font=ctk.CTkFont(family="맑은 고딕", size=12),
            text_color=record_fg,
        )
        rl.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        components["record_label"] = rl

        # 8: 최근 업데이트
        f8 = tk.Frame(
            case_frame,
            bg=bg_color,
            width=_cell_width(8),
            height=60,
            bd=0,
            highlightthickness=0,
        )
        f8.pack_propagate(False)
        frames_by_internal[8] = f8
        u_container = tk.Frame(f8, bg=bg_color)
        u_container.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        history = self.load_update_history()
        c_data = history.get(cn, {})
        last_date = (
            c_data.get("last_update", "-") if isinstance(c_data, dict) else c_data
        )
        days_since = self.get_days_since_update(case)
        date_label = ctk.CTkLabel(
            u_container,
            text=last_date,
            font=ctk.CTkFont(family="맑은 고딕", size=12),
            text_color=self.get_theme_color("text_sub"),
        )
        date_label.pack(anchor=tk.CENTER)
        d_text = "-" if days_since < 0 else f"D+{days_since}"
        d_fg = (
            self.get_theme_color("text_sub")
            if days_since < 0
            else (
                self.get_theme_color("error")
                if days_since >= 3
                else self.get_theme_color("success")
            )
        )
        d_label = ctk.CTkLabel(
            u_container,
            text=d_text,
            font=ctk.CTkFont(family="맑은 고딕", size=13, weight="bold"),
            text_color=d_fg,
        )
        d_label.pack(anchor=tk.CENTER)
        components["update_date_label"] = date_label
        components["update_d_label"] = d_label

        # 9: 시트
        f9 = tk.Frame(
            case_frame,
            bg=bg_color,
            width=_cell_width(9),
            height=60,
            bd=0,
            highlightthickness=0,
        )
        f9.pack_propagate(False)
        frames_by_internal[9] = f9
        ctk.CTkButton(
            f9,
            text="📝 시트",
            font=ctk.CTkFont(family="맑은 고딕", size=12),
            fg_color=self.get_theme_color("accent"),
            hover_color=self.get_theme_color("accent"),
            width=50,
            height=28,
            cursor="hand2",
            command=lambda idx=index: self._open_sheet_viewer(idx),
        ).place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        # col_order 순서대로 pack하고 cell_frames 구성 (헤더와 동일한 표시 순서)
        cell_frames = []
        for disp_idx, internal_idx in enumerate(self.col_order):
            frame = frames_by_internal[internal_idx]
            frame.pack(side=tk.LEFT)
            frame.pack_propagate(False)
            cell_frames.append(frame)

        self.case_frames[index] = case_frame
        return row_container, components, cell_frames

    def _validate_captcha_entry(self, index):
        """캡차 입력 6자리 숫자만 허용 (CTkEntry용)."""
        if index not in self.case_inputs:
            return
        val = self.case_inputs[index].get()
        cleaned = "".join(c for c in val if c.isdigit())[:6]
        if cleaned != val:
            self.case_inputs[index].set(cleaned)

    def update_case_list_ui(self):
        """사건 목록 UI 업데이트 (Refactored 2026)"""
        try:
            self.log_message(f"🔄 [DEBUG] UI 업데이트 시작: {len(self.case_list)}건")

            # 기존 위젯 제거
            for widget in self.case_list_frame.winfo_children():
                widget.destroy()

            self.case_checkboxes = {}
            self.case_inputs = {}
            self.case_entries = {}
            self.case_status = {}
            self.case_images = {}
            self.case_image_photos = {}
            self.case_frames = {}
            self.case_cell_frames = {}
            self.case_separators = {}
            self.case_update_labels = {}
            self.case_update_date_labels = {}
            self.case_start_times = {}
            self.case_info_text_widgets = {}

            # 컬럼 설정 (픽셀) - 저장된 값 우선, 없으면 기본값 또는 세션 리사이즈 유지
            loaded = self.load_column_widths()
            if loaded is not None and len(loaded) == len(COL_WIDTHS):
                self.col_widths = list(loaded)
            elif not hasattr(self, "col_widths") or len(self.col_widths) != len(
                COL_WIDTHS
            ):
                self.col_widths = list(COL_WIDTHS)

            # 열 표시 순서 - 저장된 값 우선, 없으면 기본 순서 (비고=맨 우측, 시트=그 왼쪽)
            order_loaded = self.load_column_order()
            if order_loaded is not None and len(order_loaded) == len(COL_NAMES):
                self.col_order = list(order_loaded)
            elif not hasattr(self, "col_order") or len(self.col_order) != len(
                COL_NAMES
            ):
                self.col_order = list(DEFAULT_COL_ORDER)

            # 전체 너비: 캔버스 너비만큼 채워 비고 열이 우측 끝까지 닿도록
            effective_total, extra_last = self._get_effective_widths()
            self._extra_width_last_col = extra_last
            if hasattr(self, "header_container") and self.header_container.winfo_exists():
                self.header_container.configure(width=effective_total)
            if hasattr(self, "header_canvas") and self.header_canvas.winfo_exists():
                self.header_canvas.configure(
                    scrollregion=(0, 0, effective_total, 40)
                )
            if hasattr(self, "case_list_frame") and self.case_list_frame.winfo_exists():
                self.case_list_frame.configure(width=effective_total)

            # 헤더 생성
            self.create_list_header()

            # 저장된 직전 상태 로드 (저장 실패/완료 등 유지)
            status_history = self.load_status_history()

            # 사건 목록 생성
            for i, case in enumerate(self.case_list):
                case_number = case.get("사건번호", "")
                initial_status = status_history.get(case_number)
                row, comps, cell_frames = self.create_case_row(
                    self.case_list_frame,
                    case,
                    i,
                    effective_total,
                    initial_status=initial_status,
                )
                self.case_cell_frames[i] = cell_frames
                self.case_info_text_widgets[i] = [
                    comps["label_info_1"],
                    comps["label_info_2"],
                    comps["label_info_3"],
                ]

                self.case_checkboxes[i] = comps["checkbox_var"]
                self.case_images[i] = comps["image_label"]
                self.case_inputs[i] = comps["captcha_var"]
                self.case_entries[i] = comps["captcha_entry"]
                self.case_status[i] = comps["status_label"]
                self.case_update_date_labels[i] = comps["update_date_label"]
                self.case_update_labels[i] = comps["update_d_label"]

            # 리스트 갱신 후 헤더 토글을 행 선택 상태에 맞춤 (전부 선택이면 체크, 아니면 해제)
            if self.case_checkboxes:
                n = len(self.case_checkboxes)
                selected_count = sum(
                    1 for v in self.case_checkboxes.values() if v.get()
                )
                self.header_select_all_var.set(selected_count == n)

            # 스크롤 영역 업데이트 (가로/세로)
            self.case_list_frame.update_idletasks()
            self.case_canvas.update_idletasks()
            self.case_canvas.configure(scrollregion=self.case_canvas.bbox("all"))
            self.case_canvas.yview_moveto(0)
            self.case_canvas.xview_moveto(0)
            if hasattr(self, "header_canvas") and self.header_canvas.winfo_exists():
                self.header_canvas.xview_moveto(0)

            # 사건 목록 내 모든 위젯에 마우스 휠 바인딩 (행/셀 위에서도 휠 스크롤 가능)
            self._bind_mousewheel_to_case_list()

            self.log_message("✅ UI 구성 완료 (Modern Style)")

        except Exception as e:
            self.log_message(f"❌ [ERROR] UI 업데이트 오류: {e}")
            import traceback

            print(traceback.format_exc())

    # _deprecated_update_case_list_ui 는 legacy/deprecated_code.py 로 옮겨 두었습니다 (참고용, 호출 안 함).

    def _on_header_select_toggle(self):
        """헤더 '전체' 체크박스 클릭 시: 체크면 전체 선택, 해제면 전체 해제."""
        if self.header_select_all_var.get():
            self.select_all_cases()
        else:
            self.deselect_all_cases()

    def _open_sheet_viewer(self, case_index):
        """사건 인덱스에 해당하는 구글 시트 데이터를 팝업에서 보기/편집."""
        if not TKSHEET_AVAILABLE:
            if not getattr(self, "_tksheet_warned", False):
                self._tksheet_warned = True
                messagebox.showwarning(
                    "라이브러리 없음",
                    "tksheet가 설치되지 않았습니다.\n"
                    "pip install tksheet 실행 후 프로그램을 다시 실행하세요.",
                )
            return
        if case_index < 0 or case_index >= len(self.case_list):
            return
        case = self.case_list[case_index]
        case_number = case.get("사건번호", "")

        popup = tk.Toplevel(self.root)
        popup.title(f"시트 보기: {case_number}")
        popup.geometry("900x500")
        popup.minsize(400, 300)

        top_bar = tk.Frame(popup)
        top_bar.pack(fill=tk.X, padx=5, pady=5)
        save_btn = tk.Button(
            top_bar,
            text="💾 구글 시트에 저장",
            font=self.get_theme_color("font_small"),
            command=lambda: None,
        )
        save_btn.pack(side=tk.LEFT)

        loading_label = tk.Label(
            popup, text="로딩 중...", font=self.get_theme_color("font_small")
        )
        loading_label.pack(expand=True)

        sheet_container = tk.Frame(popup)
        sheet_widget = [None]

        def load_done(data):
            loading_label.destroy()
            sheet_container.pack(fill=tk.BOTH, expand=True)
            sh = Sheet(
                sheet_container,
                data=data if data else [],
                headers=0,
            )
            sh.enable_bindings()
            sh.pack(fill=tk.BOTH, expand=True)
            sheet_widget[0] = sh

            def _get_sheet_data_for_save(sh):
                for method_name in ("get_sheet_data", "get_data"):
                    m = getattr(sh, method_name, None)
                    if callable(m):
                        try:
                            out = m()
                            if isinstance(out, list):
                                return out
                        except Exception:
                            continue
                return []

            def do_save():
                current = _get_sheet_data_for_save(sh)
                if not current:
                    messagebox.showinfo("저장", "저장할 데이터가 없습니다.")
                    return
                save_btn.configure(state="disabled", text="저장 중...")

                def save_thread():
                    ok = self.google_sheets_service.overwrite_sheet_data(case, current)
                    popup.after(
                        0,
                        lambda: _save_done(ok),
                    )

                t = threading.Thread(target=save_thread, daemon=True)
                t.start()

            def _save_done(ok):
                save_btn.configure(state="normal", text="💾 구글 시트에 저장")
                if ok:
                    messagebox.showinfo("저장", "구글 시트에 저장되었습니다.")
                else:
                    messagebox.showerror("저장 실패", "구글 시트 저장에 실패했습니다.")

            save_btn.configure(command=do_save)

        def fetch():
            try:
                data = self.google_sheets_service.get_full_sheet_data(case)
            except Exception as e:
                data = None
                err = str(e)
            else:
                err = None
            popup.after(0, lambda: _apply_load(data, err))

        def _apply_load(data, err):
            if err:
                loading_label.destroy()
                messagebox.showerror("시트 로드 실패", err, parent=popup)
                return
            load_done(data)

        threading.Thread(target=fetch, daemon=True).start()

    def select_all_cases(self):
        """전체 사건 선택"""
        for var in self.case_checkboxes.values():
            var.set(True)
        # 로그는 헤더 토글 사용 시 한 번만 남기도록 생략 (반복 스팸 방지)

    def deselect_all_cases(self):
        """전체 사건 해제"""
        for var in self.case_checkboxes.values():
            var.set(False)
        # 로그는 헤더 토글 사용 시 한 번만 남기도록 생략 (반복 스팸 방지)

    def get_selected_cases(self):
        """선택된 사건 목록 반환 (인덱스 포함)"""
        selected = []
        print(f"[DEBUG] 체크박스 개수: {len(self.case_checkboxes)}")
        print(f"[DEBUG] 사건 목록 개수: {len(self.case_list)}")

        for i, var in self.case_checkboxes.items():
            is_checked = var.get()
            print(
                f"[DEBUG] 사건 {i}: {self.case_list[i].get('사건번호', '')} - 체크됨: {is_checked}"
            )
            if is_checked:
                # (원래 인덱스, 사건 데이터) 튜플로 반환
                selected.append((i, self.case_list[i]))

        print(f"[DEBUG] 선택된 사건 수: {len(selected)}")
        return selected

    def on_checkbox_change(self, index):
        """체크박스 변경 이벤트 핸들러. 행 선택 개수에 따라 헤더 토글도 동기화."""
        is_checked = self.case_checkboxes[index].get()
        case_number = self.case_list[index].get("사건번호", "")
        print(f"[DEBUG] 체크박스 변경: {case_number} - 체크됨: {is_checked}")
        # 헤더 토글 반영: 모두 선택이면 헤더 체크, 아니면 헤더 해제
        if self.case_checkboxes:
            n = len(self.case_checkboxes)
            selected_count = sum(1 for v in self.case_checkboxes.values() if v.get())
            self.header_select_all_var.set(selected_count == n)

    def start_batch_processing(self):
        """
        캡차 이미지 로드 시작 함수

        사용자가 "캡차 이미지 로드" 버튼을 클릭했을 때 호출됩니다.

        처리 순서:
        1. 선택된 사건들을 가져옵니다
        3. 선택된 사건이 없으면 경고를 표시합니다
        4. 이미 처리 중이면 경고를 표시합니다
        5. 백그라운드 스레드에서 캡차 이미지를 로드합니다

        주의: 이 함수는 캡차 이미지만 로드하고, 실제 크롤링은
        "캡차 입력 완료" 버튼을 클릭했을 때 실행됩니다.
        """
        print("[DEBUG] 캡차 이미지 로드 버튼 클릭됨")

        # ============================================================
        # 1단계: 선택된 사건들 가져오기
        # ============================================================
        # get_selected_cases()는 (인덱스, 사건데이터) 튜플 리스트를 반환
        # 예: [(0, {'사건번호': '2023가합10019', ...}), (2, {...}), ...]
        selected_cases_with_index = self.get_selected_cases()
        # 튜플에서 사건 데이터만 추출 (인덱스는 버림)
        selected_cases = [case for _, case in selected_cases_with_index]

        # ============================================================
        # 2단계: 유효성 검사 (선택된 사건이 있는지 확인)
        # ============================================================
        if not selected_cases:
            print("[DEBUG] 선택된 사건이 없음 - 경고 표시")
            # 경고 메시지 박스 표시 (사용자에게 알림)
            messagebox.showwarning("경고", "처리할 사건을 선택해주세요.")
            return  # 함수 종료 (더 이상 진행 안 함)

        # ============================================================
        # 3단계: 중복 실행 방지 (이미 처리 중인지 확인)
        # ============================================================
        if self.processing:
            print("[DEBUG] 이미 처리 중 - 경고 표시")
            messagebox.showwarning("경고", "이미 처리 중입니다.")
            return  # 함수 종료

        print(f"[DEBUG] {len(selected_cases)}개 사건 선택됨 - 캡차 이미지 로드 시작")

        # ============================================================
        # 4단계: Wave Processing 초기화
        # ============================================================
        # 처리된 사건 추적용 집합 초기화
        self.processed_cases = set()

        # ============================================================
        # 5단계: UI 상태 변경 (버튼 비활성화 등)
        # ============================================================
        # 처리 중 플래그를 True로 설정
        self.processing = True
        # 시작 버튼을 "로딩 중..."으로 변경하고 비활성화
        self.start_btn.configure(text="🔄 로딩 중...")
        self._set_control_btn_state(self.start_btn, False)
        self._set_control_btn_state(self.stop_btn, True)

        # ============================================================
        # 6단계: 백그라운드 스레드에서 처리 시작
        # ============================================================
        # threading.Thread: 별도 스레드(작업 흐름)를 만들어서 실행
        # target: 실행할 함수 (execute_actual_processing)
        # args: 함수에 전달할 인자들 (선택된 사건 리스트)
        # daemon=True: 메인 프로그램이 종료되면 이 스레드도 자동 종료
        self.processing_thread = threading.Thread(
            target=self.execute_actual_processing, args=(selected_cases,)
        )
        self.processing_thread.daemon = True
        # 스레드 시작 (백그라운드에서 실행됨, GUI는 계속 응답함)
        self.processing_thread.start()

    def stop_batch_processing(self):
        """일괄 처리 중지"""
        self.processing = False
        for ev in getattr(self, "lane_events", {}).values():
            ev.set()
        self.start_btn.configure(text="🖼️ 사건 조회 로드 실행\n(캡차 로드 실행)")
        self._set_control_btn_state(self.start_btn, True)
        self._set_control_btn_state(self.stop_btn, False)
        self.log_message("⏹️ 처리 중지됨")

    def cleanup_case_process(self, case_number):
        """
        개별 사건의 브라우저 프로세스 정리

        Args:
            case_number: 사건번호
        """
        try:
            if case_number in self.browser_processes:
                process = self.browser_processes[case_number]
                try:
                    if process.poll() is None:
                        self.log_message(f"🔄 프로세스 종료 중: {case_number}")
                        process.kill()
                        try:
                            process.wait(timeout=2)
                        except:
                            pass
                        self.log_message(f"✅ 프로세스 종료 완료: {case_number}")
                except Exception as e:
                    self.log_message(f"⚠️ 프로세스 종료 실패: {case_number} - {e}")

                # 딕셔너리에서 제거
                del self.browser_processes[case_number]

            if case_number in self.browser_ws_urls:
                del self.browser_ws_urls[case_number]

        except Exception as e:
            self.log_message(f"⚠️ 프로세스 정리 오류: {case_number} - {e}")

    def _lane_for_case(self, case_number, n_lanes):
        """전용 차로: 사건번호 기준으로 고정된 방(0~n_lanes-1) 반환"""
        import hashlib

        h = int(hashlib.md5(case_number.encode("utf-8")).hexdigest(), 16)
        return h % n_lanes

    def get_case_profile_index(self, case_number):
        """사건번호에 따른 고정 프로필(인스턴스) 번호 반환. 쿠키/스마트스킵 유지용."""
        import hashlib

        max_profiles = getattr(config, "MAX_PARALLEL_LIMIT", 20)
        h = int(hashlib.md5(case_number.encode("utf-8")).hexdigest(), 16)
        return h % max_profiles

    def execute_actual_processing(self, cases):
        """실제 처리 실행 (전용 차로제: 그룹별 순차, 그룹끼리 병렬)"""
        if not cases:
            return

        self.lane_events = {}
        self.log_message("🔄 병렬 처리 시작 (전용 차로제)")

        max_limit = getattr(config, "MAX_PARALLEL_LIMIT", 20)
        n_lanes = min(self.max_parallel.get(), len(cases), max_limit)
        if n_lanes < 1:
            n_lanes = 1

        # 사건을 차로별로 분배 (같은 사건은 항상 같은 차로)
        lanes = [[] for _ in range(n_lanes)]
        for case in cases:
            case_number = case.get("사건번호", "")
            case_index = self.find_case_index(case_number)
            if case_index == -1 or case_index not in self.case_images:
                continue
            lane = self._lane_for_case(case_number, n_lanes)
            lanes[lane].append((case, case_index))

        def run_lane(lane_index, queue):
            for case, case_index in queue:
                if not self.processing:
                    return
                self.process_single_case_parallel(case, case_index, lane_index)

        threads = []
        for i in range(n_lanes):
            if not lanes[i]:
                continue
            t = threading.Thread(target=run_lane, args=(i, lanes[i]))
            t.daemon = True
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        self.log_message("🎉 모든 캡차 이미지 로드 완료!")
        self.processing = False
        # 버튼 상태 변경 (Thread-Safe)
        def _restore_start_btn():
            self.start_btn.configure(text="🖼️ 사건 조회 로드 실행\n(캡차 로드 실행)")
            self._set_control_btn_state(self.start_btn, True)

        self.root.after(0, _restore_start_btn)
        self.root.after(0, lambda: self._set_control_btn_state(self.stop_btn, False))

    def _process_auto_case(self, case, case_index):
        """
        자동 클릭 케이스 즉시 처리 (Smart Auto-Pass)

        Args:
            case: 사건 정보 딕셔너리
            case_index: 사건 인덱스

        Returns:
            bool: 처리 성공 여부
        """
        case_number = case.get("사건번호", "")
        import time

        try:
            self.log_message(f"⚡ 캡차 스킵: 자동 처리 시작 - {case_number}")

            # 자동 클릭 처리 실행
            result_data = self.execute_case_processing(case, "CLICK")

            if (
                isinstance(result_data, dict)
                and result_data.get("status") == "WRONG_CAPTCHA"
            ):
                self.log_message("⚠️ 자동 클릭 중 캡차 불일치 - 재시도 필요")
                self.update_case_status(case_index, "재입력대기", "red", "⚠️")
                return False

            if isinstance(result_data, list):
                elapsed_time = int(
                    time.time() - self.case_start_times.get(case_index, time.time())
                )
                try:
                    last_entry_result = (
                        self.google_sheets_service.get_last_entry_from_sheet(case)
                    )
                    if last_entry_result is not None:
                        last_entry, sheet_last_row_index = last_entry_result
                        self.log_message(
                            f"📋 [DEBUG] 구글 시트 기준 비교: {case_number}"
                        )
                    else:
                        last_entry = None
                        sheet_last_row_index = None
                except Exception as e:
                    self.log_message(f"⚠️ 시트 조회 실패, 로컬 기록 사용: {e}")
                    last_entry = self.history_manager.get_last_entry(case_number)
                    sheet_last_row_index = None
                new_data = self.filter_new_data(result_data, last_entry)

                # 변경없음(빈 리스트)이지만 시트 행 개수가 부족한 경우(기일 등이 마지막에 있어 중간 삽입 발생)
                # 기일 행을 삭제한 뒤, 새 데이터 + 기일을 순서대로 다시 추가
                if not new_data and sheet_last_row_index is not None:
                    sheet_data_count = sheet_last_row_index - 1
                    current_len = len(result_data)
                    if sheet_data_count < current_len:
                        missing = current_len - sheet_data_count
                        if self.google_sheets_service.delete_specific_row(
                            case, sheet_last_row_index
                        ):
                            new_data = result_data[-(missing + 1) :]
                            self.log_message(
                                f"⚠️ [보정] 기일 행 제거 후 +{missing + 1}건 추가 (기일 순서 유지)"
                            )
                        else:
                            new_data = result_data[-missing:]
                            self.log_message(
                                f"⚠️ [보정] 시트 누락: +{missing}건 강제 추가 (행 삭제 실패)"
                            )
                if not new_data:
                    self.log_message(f"📭 변경없음: {case_number}")
                    self.update_case_status(
                        case_index, "완료 (변경없음)", "#7F8C8D", "✅"
                    )
                    history = self.load_update_history()
                    prev_total = 0
                    if isinstance(history.get(case_number), dict):
                        prev_total = history.get(case_number, {}).get("row_count", 0)
                    current_count = (
                        len(result_data) if isinstance(result_data, list) else 0
                    )
                    new_total = max(prev_total, current_count)
                    self.update_case_timestamp(case, case_index, new_total)
                    if hasattr(self, "processed_cases"):
                        self.processed_cases.add(case_index)
                    self.log_message(
                        f"✅ 자동 처리 완료: {case_number} (소요 시간: {elapsed_time}초)"
                    )
                    return True
                row_count = None
                try:
                    row_count = self.save_to_google_sheets(case, new_data)
                except Exception as save_err:
                    self.log_message(f"❌ 구글 시트 저장 예외: {save_err}")
                    row_count = False
                if row_count is False or row_count is None:
                    self.update_case_status(case_index, "저장 실패", "red", "❌")
                    self.log_message(f"❌ 구글 시트 저장 실패: {case_number}")
                    return False
                if row_count == 0:
                    self.update_case_status(case_index, "데이터 없음", "#7F8C8D", "📭")
                else:
                    self.history_manager.update_last_entry(case_number, new_data[-1])
                    self.google_sheets_service.update_main_remark(
                        case_number, row_count
                    )
                    self.update_case_status(
                        case_index, f"완료 (+{row_count}건)", "green", "✅"
                    )
                history = self.load_update_history()
                old_total = 0
                if isinstance(history.get(case_number), dict):
                    old_total = history.get(case_number, {}).get("row_count", 0)
                total_rows = (old_total + row_count) if row_count else old_total
                self.update_case_timestamp(case, case_index, total_rows)
                if row_count > 0:
                    self.add_to_search_log(case_number)
                if hasattr(self, "processed_cases"):
                    self.processed_cases.add(case_index)
                self.log_message(
                    f"✅ 자동 처리 완료: {case_number} (소요 시간: {elapsed_time}초)"
                )
                return True
            else:
                # 실패 처리
                elapsed_time = int(
                    time.time() - self.case_start_times.get(case_index, time.time())
                )
                self.update_case_status(case_index, "실패", "red", "❌")
                self.log_message(f"❌ 자동 처리 실패: {case_number}")
                return False

        except Exception as e:
            elapsed_time = int(
                time.time() - self.case_start_times.get(case_index, time.time())
            )
            self.update_case_status(case_index, f"오류 ({elapsed_time}초)", "red", "⚠️")
            self.log_message(f"❌ 자동 처리 오류: {case_number} - {e}")
            return False
        finally:
            # 항상 프로세스 정리
            self.cleanup_case_process(case_number)

            # 이벤트 해제
            ev = getattr(self, "lane_events", {}).pop(case_number, None)
            if ev:
                ev.set()

    def process_single_case_parallel(self, case, case_index, instance_index=0):
        """병렬 처리용 단일 사건 처리. 사건번호별 고정 프로필(인스턴스) 사용 + 프로필 락."""
        case_number = case.get("사건번호", "")
        profile_index = self.get_case_profile_index(case_number)

        try:
            import time

            self.case_start_times[case_index] = time.time()
            self.update_case_status(case_index, "처리중(캡차로딩)", "orange", "🔄")

            # 동일 프로필 폴더 동시 사용 방지 (같은 사건번호는 항상 같은 instance_N 사용)
            with self.profile_locks[profile_index]:
                result_data = self.execute_case_processing_with_captcha(
                    case, case_index, profile_index
                )

            # 처리 시간 계산
            elapsed_time = int(time.time() - self.case_start_times[case_index])

            if result_data:
                # [SMART SKIP] 캡차 스킵 모드 처리
                if result_data == "__CLICK__":
                    # 캡차 입력란에 "CLICK" 자동 입력
                    if case_index in self.case_inputs:
                        self.case_inputs[case_index].set("CLICK")

                    self.update_case_status(case_index, "입력완료", "green", "⚡")
                    self.log_message(
                        f"⚡ 캡차 스킵: {case_number} (자동 클릭 준비 완료)"
                    )
                    # 자동 처리 즉시 실행
                    self._process_auto_case(case, case_index)
                    return True

                # 캡차 이미지 로드만 완료된 상태 (실제 크롤링은 "캡차 입력 완료" 버튼 클릭 후 실행)
                self.update_case_status(case_index, "입력대기", "blue", "⏳")
                self.log_message(
                    f"✅ 캡차 이미지 로드 완료: {case_number} (소요 시간: {elapsed_time}초)"
                )
                # 완료 버튼 활성화
                self.root.after(0, lambda: self._set_control_btn_state(self.complete_btn, True))
                ev = threading.Event()
                self.lane_events[case_number] = ev
                ev.wait()
                return True
            else:
                self.update_case_status(
                    case_index, f"실패 ({elapsed_time}초)", "red", "❌"
                )
                return False

        except Exception as e:
            elapsed_time = int(
                time.time() - self.case_start_times.get(case_index, time.time())
            )
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
                self.log_message(
                    f"✅ 캡차 입력 저장: {captcha_input} (사건 인덱스: {case_index}) - 길이: {len(captcha_input)}"
                )
                # 상태를 "입력완료"로 변경 (실제 처리는 하지 않음)
                self.update_case_status(case_index, "입력완료", "blue")

                # 다음 입력칸으로 포커스 이동
                self.move_to_next_input(case_index)
            else:
                self.log_message(
                    f"⚠️ 캡차 입력 형식 오류: {captcha_input} (길이: {len(captcha_input)}, 숫자여부: {captcha_input.isdigit()})"
                )
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
                            if (
                                isinstance(grandchild, tk.Entry)
                                and grandchild.grid_info().get("row") == 0
                                and grandchild.grid_info().get("column") == 6
                            ):
                                entry_widget = grandchild
                                break
                        if entry_widget:
                            break

                if entry_widget:
                    entry_widget.focus()
                    self.log_message(
                        f"🔄 다음 입력칸으로 이동: 사건 인덱스 {next_index}"
                    )
                else:
                    self.log_message("⚠️ 입력칸을 찾을 수 없습니다")
            else:
                self.log_message("ℹ️ 다음 입력할 사건이 없습니다")

        except Exception as e:
            self.log_message(f"⚠️ 다음 입력칸 이동 실패: {e}")

    def start_processing_thread(self):
        """별도 스레드에서 캡차 입력 처리를 시작 (GUI 멈춤 방지)"""
        processing_thread = threading.Thread(
            target=self.process_all_captcha_inputs, daemon=True
        )
        processing_thread.start()
        self.log_message("🚀 백그라운드 처리 시작 - GUI는 계속 응답합니다!")

    def _process_one_case(
        self, original_index, case, total_cases, total_start_time, selected_cases
    ):
        """
        선택된 사건 하나에 대해 캡차 검증·실행·저장·GUI 갱신을 수행합니다.
        process_all_captcha_inputs 루프 안에서만 호출됩니다.
        반환: (completed_delta, failed_delta) — 각각 0 또는 1.
        """
        import time

        case_number = case.get("사건번호", "")
        try:
            if original_index not in self.case_inputs:
                return (0, 0)

            captcha_input = self.get_captcha_input(original_index)
            self.log_message(f"📋 [DEBUG] 캡차 입력값: '{captcha_input}'")
            case_start_time = time.time()
            self.case_start_times[original_index] = case_start_time

            current_progress = len(
                [
                    i
                    for i, _ in selected_cases[
                        : selected_cases.index((original_index, case)) + 1
                    ]
                ]
            )
            progress_percent = (current_progress / total_cases) * 100
            elapsed = int(time.time() - total_start_time)
            if current_progress > 0:
                avg_time = elapsed / current_progress
                remaining_time = int(avg_time * (total_cases - current_progress))
                self.update_progress(
                    progress_percent,
                    f"🔄 처리 중... ({current_progress}/{total_cases}) - {case_number} | 예상 남은 시간: {remaining_time}초",
                )
            else:
                self.update_progress(
                    progress_percent,
                    f"🔄 처리 중... ({current_progress}/{total_cases}) - {case_number}",
                )

            if not (captcha_input and captcha_input.strip()):
                self.log_message(f"⚠️ 캡차 입력이 비어있음: {case_number}")
                self.update_case_status(original_index, "입력없음", "red", "⚠️")
                return (0, 1)

            self.log_message(
                f"📋 [DEBUG] GUI에서 가져온 캡차 입력: '{captcha_input}' (타입: {type(captcha_input).__name__}, 길이: {len(captcha_input)})"
            )
            is_click = captcha_input == "CLICK"
            is_valid_captcha = len(captcha_input) == 6 and captcha_input.isdigit()
            if not (is_click or is_valid_captcha):
                self.log_message(
                    f"⚠️ 캡차 입력 형식 오류: {case_number} (입력: {captcha_input}, 길이: {len(captcha_input)})"
                )
                self.update_case_status(original_index, "형식오류", "red", "⚠️")
                return (0, 1)

            self.log_message(f"✅ [DEBUG] 캡차 형식 검증 통과: {captcha_input}")
            self.log_message(f"🔄 처리 시작: {case_number} (캡차: {captcha_input})")
            self.update_case_status(original_index, "처리중(크롤링)", "orange", "🔄")

            self.log_message(f"🔄 [DEBUG] execute_case_processing 호출 전")
            should_cleanup_and_release = True
            result_data = self.execute_case_processing(case, captcha_input.strip())
            self.log_message(
                f"🔄 [DEBUG] execute_case_processing 호출 후 - result_data 타입: {type(result_data)}"
            )
            elapsed_time = int(time.time() - case_start_time)

            try:
                # 캡차 불일치: 재입력 대기 (프로세스 유지, 이벤트 유지)
                if (
                    isinstance(result_data, dict)
                    and result_data.get("status") == "WRONG_CAPTCHA"
                ):
                    self.log_message("⚠️ 캡차 불일치 - 재시도 필요")
                    new_path = result_data.get("image_path")
                    if new_path:
                        self.root.after(
                            0,
                            lambda p=new_path, i=original_index: self.update_captcha_image(
                                i, p
                            ),
                        )
                    self.update_case_status(original_index, "재입력대기", "red", "⚠️")
                    should_cleanup_and_release = False
                    return (0, 0)

                if isinstance(result_data, list):
                    # 증분 저장: 구글 시트 실제 마지막 행 기준 비교, 없으면 로컬 캐시
                    try:
                        last_entry_result = (
                            self.google_sheets_service.get_last_entry_from_sheet(case)
                        )
                        if last_entry_result is not None:
                            last_entry, sheet_last_row_index = last_entry_result
                            self.log_message(
                                f"📋 [DEBUG] 구글 시트 기준 비교: {case_number}"
                            )
                        else:
                            last_entry = None
                            sheet_last_row_index = None
                    except Exception as e:
                        self.log_message(f"⚠️ 시트 조회 실패, 로컬 기록 사용: {e}")
                        last_entry = self.history_manager.get_last_entry(case_number)
                        sheet_last_row_index = None
                    new_data = self.filter_new_data(result_data, last_entry)

                    # 변경없음(빈 리스트)이지만 시트 행 개수가 부족한 경우(기일 등이 마지막에 있어 중간 삽입 발생)
                    # 기일 행을 삭제한 뒤, 새 데이터 + 기일을 순서대로 다시 추가
                    if not new_data and sheet_last_row_index is not None:
                        sheet_data_count = sheet_last_row_index - 1
                        current_len = len(result_data)
                        if sheet_data_count < current_len:
                            missing = current_len - sheet_data_count
                            if self.google_sheets_service.delete_specific_row(
                                case, sheet_last_row_index
                            ):
                                new_data = result_data[-(missing + 1) :]
                                self.log_message(
                                    f"⚠️ [보정] 기일 행 제거 후 +{missing + 1}건 추가 (기일 순서 유지)"
                                )
                            else:
                                new_data = result_data[-missing:]
                                self.log_message(
                                    f"⚠️ [보정] 시트 누락: +{missing}건 강제 추가 (행 삭제 실패)"
                                )
                    if not new_data:
                        self.log_message(f"📭 변경없음: {case_number}")
                        self.update_case_status(
                            original_index, "완료 (변경없음)", "#7F8C8D", "✅"
                        )
                        history = self.load_update_history()
                        prev_total = 0
                        if isinstance(history.get(case_number), dict):
                            prev_total = history.get(case_number, {}).get(
                                "row_count", 0
                            )
                        current_count = (
                            len(result_data) if isinstance(result_data, list) else 0
                        )
                        new_total = max(prev_total, current_count)
                        self.update_case_timestamp(case, original_index, new_total)
                        self.log_message(
                            f"✅ 처리 완료: {case_number} (소요 시간: {elapsed_time}초)"
                        )
                        return (1, 0)
                    row_count = None
                    try:
                        row_count = self.save_to_google_sheets(case, new_data)
                    except Exception as save_err:
                        self.log_message(f"❌ 구글 시트 저장 예외: {save_err}")
                        row_count = False
                    if row_count is False or row_count is None:
                        self.update_case_status(
                            original_index, "저장 실패", "red", "❌"
                        )
                        self.log_message(f"❌ 구글 시트 저장 실패: {case_number}")
                        return (0, 1)
                    if row_count == 0:
                        self.update_case_status(
                            original_index, "데이터 없음", "#7F8C8D", "📭"
                        )
                    else:
                        self.history_manager.update_last_entry(
                            case_number, new_data[-1]
                        )
                        self.google_sheets_service.update_main_remark(
                            case_number, row_count
                        )
                        self.update_case_status(
                            original_index,
                            f"완료 (+{row_count}건)",
                            "green",
                            "✅",
                        )
                    # 타임스탬프용 총 행 수 (기존 + 이번에 추가한 행)
                    history = self.load_update_history()
                    old_total = 0
                    if isinstance(history.get(case_number), dict):
                        old_total = history.get(case_number, {}).get("row_count", 0)
                    total_rows = (old_total + row_count) if row_count else old_total
                    self.update_case_timestamp(case, original_index, total_rows)
                    if row_count > 0:
                        self.add_to_search_log(case_number)
                    self.log_message(
                        f"✅ 처리 완료: {case_number} (소요 시간: {elapsed_time}초)"
                    )
                    return (1, 0)
                else:
                    self.update_case_status(
                        original_index, f"실패 ({elapsed_time}초)", "red", "❌"
                    )
                    self.log_message(f"❌ 처리 실패: {case_number}")
                    return (0, 1)
            except Exception as e:
                self.log_message(f"❌ [DEBUG] 사건 처리 중 예외 발생: {e}")
                import traceback

                self.log_message(f"❌ [DEBUG] 예외 스택: {traceback.format_exc()}")
                self.update_case_status(
                    original_index, f"오류 ({elapsed_time}초)", "red", "⚠️"
                )
                return (0, 1)
        finally:
            if should_cleanup_and_release:
                self.cleanup_case_process(case_number)
                if hasattr(self, "processed_cases"):
                    self.processed_cases.add(original_index)
                ev = getattr(self, "lane_events", {}).pop(case_number, None)
                if ev:
                    ev.set()

    def process_all_captcha_inputs(self):
        """
        모든 캡차 입력을 한번에 처리하는 함수.

        호출 시점: 사용자가 "캡차 입력 완료" 버튼을 클릭하면 start_processing_thread() 가 이 메서드를 백그라운드 스레드에서 실행합니다.
        스레드에서 돌기 때문에 GUI 업데이트는 반드시 self.root.after(0, ...) 로 메인 스레드에 넘겨야 합니다.

        처리 순서:
        1. 선택된 모든 사건을 가져옵니다
        2. 각 사건의 캡차 입력값을 확인합니다
        3. 캡차가 입력된 사건부터 순서대로 처리합니다
        4. Puppeteer를 통해 웹 크롤링을 실행합니다
        5. 결과를 구글 시트에 저장합니다
        6. 모든 브라우저 프로세스를 종료합니다

        주의: 이 함수는 스레드에서 실행되므로 GUI 업데이트는
        self.root.after()를 사용해야 합니다 (Thread-Safe).
        """
        try:
            import time

            total_start_time = time.time()
            self.processing = True
            self.puppeteer_service.processing_flag = lambda: self.processing
            self.log_message("🔄 모든 캡차 입력 처리 시작")

            # 완료 버튼 명시적으로 비활성화 (처리 시작 시)
            self.root.after(0, lambda: self._set_control_btn_state(self.complete_btn, False))

            # Wave Processing: processed_cases 초기화 (없으면 생성)
            if not hasattr(self, "processed_cases"):
                self.processed_cases = set()

            self.root.after(0, lambda: self._set_control_btn_state(self.start_btn, False))
            self.root.after(0, lambda: self._set_control_btn_state(self.stop_btn, True))

            selected_cases = self.get_selected_cases()
            total_cases = len(selected_cases)
            self.update_progress(0, f"⏳ 처리 준비 중... (0/{total_cases})")
            completed = 0
            failed = 0

            self.log_message(f"🔄 [DEBUG] 처리할 사건 목록: {len(selected_cases)}개")
            for idx, (original_index, case) in enumerate(selected_cases):
                if not self.processing:
                    self.log_message(f"⏹️ 사용자가 처리를 중지했습니다")
                    break

                # Wave Processing: 현재 차로에서 대기 중인 사건만 처리
                case_number = case.get("사건번호", "")
                if case_number not in getattr(self, "lane_events", {}):
                    continue

                c_delta, f_delta = self._process_one_case(
                    original_index, case, total_cases, total_start_time, selected_cases
                )
                completed += c_delta
                failed += f_delta
                self.log_message(
                    f"🔄 [DEBUG] 루프 끝: {idx+1}/{len(selected_cases)} - 인덱스={original_index}"
                )

            self.log_message(
                f"🔄 [DEBUG] 현재 파도 처리 완료 - 성공: {completed}, 실패: {failed}"
            )

            # Wave Processing: 남은 사건 수 계산
            pending_count = len(selected_cases) - len(
                getattr(self, "processed_cases", set())
            )

            if pending_count > 0:
                # 다음 파도 대기 중
                self.log_message(
                    f"⏳ 다음 파도 대기 중... (남은 사건: {pending_count}건)"
                )
                # "Captcha Input Complete" 버튼 재활성화 (다음 파도 준비)
                self.root.after(0, lambda: self._set_control_btn_state(self.complete_btn, True))
                # processing 플래그는 유지 (아직 처리 중)
                # Chrome 정리는 하지 않음 (다음 파도에서 사용)
            else:
                # 모든 사건 처리 완료
                self.log_message("🎉 모든 사건 처리 완료!")

                # Chrome 프로세스 정리
                try:
                    import subprocess as sp
                    import psutil

                    self.log_message(f"🔄 [DEBUG] Chrome 프로세스 정리 중...")

                    # psutil로 Chrome 프로세스 찾아서 종료
                    chrome_killed = 0
                    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                        try:
                            # Chrome 프로세스이고 --remote-debugging-port가 있으면
                            if (
                                proc.info["name"]
                                and "chrome.exe" in proc.info["name"].lower()
                            ):
                                cmdline = proc.info.get("cmdline", [])
                                if cmdline and any(
                                    "--remote-debugging-port" in str(arg)
                                    for arg in cmdline
                                ):
                                    self.log_message(
                                        f"🔄 [DEBUG] Chrome 프로세스 종료: PID {proc.info['pid']}"
                                    )
                                    proc.kill()  # 강제 종료
                                    chrome_killed += 1
                        except (
                            psutil.NoSuchProcess,
                            psutil.AccessDenied,
                            psutil.ZombieProcess,
                        ):
                            pass

                    if chrome_killed > 0:
                        self.log_message(
                            f"✅ Chrome 프로세스 {chrome_killed}개 종료 완료"
                        )
                    else:
                        self.log_message(f"ℹ️ 종료할 Chrome 프로세스 없음")

                except Exception as e:
                    self.log_message(f"⚠️ Chrome 프로세스 정리 오류: {e}")
                    # 최후의 수단: taskkill 사용
                    try:
                        sp.run(
                            ["taskkill", "/F", "/IM", "chrome.exe"],
                            capture_output=True,
                            timeout=3,
                        )
                        self.log_message(f"⚠️ taskkill로 Chrome 강제 종료 시도")
                    except:
                        pass

                self.browser_processes.clear()
                self.browser_ws_urls.clear()
                self.log_message(f"✅ 모든 브라우저 프로세스 종료 완료")

                # 총 처리 시간
                total_elapsed = int(time.time() - total_start_time)

                # 최종 진행률 업데이트
                self.update_progress(
                    100,
                    f"✅ 처리 완료! (성공: {completed}, 실패: {failed}) | 총 소요 시간: {total_elapsed}초",
                )
                self.log_message(
                    f"🎉 모든 캡차 입력 처리 완료! (총 소요 시간: {total_elapsed}초)"
                )

                # 완료 알림 MessageBox (Thread-Safe)
                self.root.after(
                    0,
                    lambda: messagebox.showinfo(
                        "처리 완료",
                        f"🎉 처리가 완료되었습니다!\n\n"
                        f"✅ 성공: {completed}개\n"
                        f"❌ 실패: {failed}개\n"
                        f"📊 총 사건: {total_cases}개\n"
                        f"⏱️ 총 소요 시간: {total_elapsed}초",
                    ),
                )

                # 처리 완료 - 버튼 상태 복원 (Thread-Safe)
                self.processing = False
                self.root.after(
                    0, lambda: self._set_control_btn_state(self.complete_btn, False)
                )
                def _restore_start():
                    self.start_btn.configure(
                        text="🖼️ 사건 조회 로드 실행\n(캡차 로드 실행)"
                    )
                    self._set_control_btn_state(self.start_btn, True)

                self.root.after(0, _restore_start)
                self.root.after(
                    0, lambda: self._set_control_btn_state(self.stop_btn, False)
                )

        except Exception as e:
            self.log_message(f"❌ 캡차 입력 처리 오류: {e}")
            self.update_progress(0, "오류 발생")
            # 버튼 상태 복원 (Thread-Safe)
            self.root.after(0, lambda: self._set_control_btn_state(self.complete_btn, True))
            def _restore_start():
                self.start_btn.configure(
                    text="🖼️ 사건 조회 로드 실행\n(캡차 로드 실행)"
                )
                self._set_control_btn_state(self.start_btn, True)

            self.root.after(0, _restore_start)
            self.root.after(
                0, lambda: self._set_control_btn_state(self.stop_btn, False)
            )
            # 오류 발생 시에도 처리 상태 해제
            self.processing = False

    def process_after_captcha_input(self, case_index, captcha_input):
        """캡차 입력 후 실제 처리 (사용하지 않음)"""
        pass

    def process_single_case(self, case, case_index):
        """단일 사건 처리"""
        case_number = case.get("사건번호", "")
        defendant = case.get("피고", "")
        court = case.get("법원", "")
        max_retry = self.max_retry.get()

        # 상태 업데이트: 단일 사건 처리 시도 시작 (재시도 루프)
        self.update_case_status(case_index, "처리중(시도)", "orange")

        for attempt in range(max_retry + 1):
            try:
                self.log_message(
                    f"📋 처리 시도 {attempt + 1}/{max_retry + 1}: {case_number}"
                )

                # 1. 캡차 이미지 캡처 (전용 차로: 단일 플로우는 instance 0)
                image_path = self.capture_captcha_image(
                    case_number, defendant, court, instance_index=0
                )

                # 2. 캡차 이미지 표시
                self.update_captcha_image(case_index, image_path)

                # 3. 캡차 입력 필드 활성화 및 대기
                self.update_case_status(case_index, "캡차입력", "blue")
                self.log_message(f"🔐 캡차 입력 대기: {case_number}")

                # 완료 버튼 활성화
                self._set_control_btn_state(self.complete_btn, True)

                # 사용자가 캡차를 입력할 때까지 대기 (대기 시간: config.CAPTCHA_INPUT_TIMEOUT초)
                captcha_input = self.wait_for_captcha_input(
                    case_index, timeout_seconds=config.CAPTCHA_INPUT_TIMEOUT
                )

                if captcha_input is None:
                    self.log_message(f"❌ 취소됨: {case_number}")
                    self.update_case_status(case_index, "취소", "red")
                    return False

                # 3. 캡차 입력 검증 (임시 - 실제로는 웹사이트에서)
                if self.validate_captcha(captcha_input):
                    self.log_message(f"✅ 캡차 검증 성공: {case_number}")
                    self.update_case_status(case_index, "처리중(저장)", "orange")
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
                    self.log_message(
                        f"❌ 캡차 검증 실패: {case_number} (시도 {attempt + 1})"
                    )
                    self.update_case_status(
                        case_index, f"재시도{attempt + 1}", "yellow"
                    )
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

    def capture_captcha_image(self, case_number, defendant, court, instance_index=0):
        """
        캡차 이미지 캡처 (실제 Puppeteer 실행, 전용 차로: instance_index)

        services/puppeteer.py의 PuppeteerService를 사용합니다.
        """
        try:
            # PuppeteerService를 사용하여 캡차 이미지 캡처 (cookie_data_for_save/instance_N)
            image_path, ws_url, process = self.puppeteer_service.capture_captcha_image(
                case_number, defendant, court, instance_index
            )

            # WebSocket URL과 프로세스 저장
            if ws_url:
                self.browser_ws_urls[case_number] = ws_url
            if process:
                self.browser_processes[case_number] = process

                return image_path

        except Exception as e:
            self.log_message(f"❌ 캡차 이미지 캡처 오류: {e}")
            return None

    def validate_captcha(self, captcha_input):
        """캡차 입력 검증 (임시 구현)"""
        # 실제로는 여기서 웹사이트에 캡차 입력 후 응답 확인
        # 임시로 랜덤 성공/실패
        import random

        return random.choice([True, True, False])  # 66% 성공률

    def execute_case_processing_with_captcha(self, case, case_index, instance_index=0):
        """캡차 이미지만 캡처하고 GUI에 표시 (전용 차로: instance_index)"""
        try:
            case_number = case.get("사건번호", "")
            defendant = case.get("피고", "")
            court = case.get("법원", "")

            self.log_message(f"🔄 처리 시작: {case_number} (법원: {court})")

            # 1. 먼저 캡차 이미지만 캡처 (전용 인스턴스 사용)
            self.log_message(f"📸 캡차 이미지 캡처 중: {case_number}")
            image_path = self.capture_captcha_image(
                case_number, defendant, court, instance_index
            )

            if image_path:
                # 2. GUI에 캡차 이미지 표시
                self.update_captcha_image(case_index, image_path)
                self.update_case_status(case_index, "캡차입력", "blue")
                self.log_message(f"🔐 캡차 입력 대기: {case_number}")

                # 3. 완료 버튼 활성화 (Thread-Safe)
                self.root.after(0, lambda: self._set_control_btn_state(self.complete_btn, True))
                self.log_message(f"✅ 캡차 입력 완료 버튼 활성화됨")

                return image_path
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
            for line in stdout.split("\n"):
                if "GUI_IMAGE_PATH:" in line:
                    image_path = line.split("GUI_IMAGE_PATH: ")[1].strip()
                    break

            # JSON 결과가 있는지 확인
            if "case_result_" in stdout:
                # JSON 파일에서 결과 읽기
                result_files = glob.glob("results/case_result_*.json")
                if result_files:
                    latest_file = max(result_files, key=os.path.getctime)
                    with open(latest_file, "r", encoding="utf-8") as f:
                        result_data = json.load(f)
                    if image_path:
                        result_data["image_path"] = image_path
                    return result_data

            return {"success": True, "message": "처리 완료", "image_path": image_path}
        except Exception as e:
            self.log_message(f"❌ 결과 파싱 오류: {e}")
            return {"success": False, "message": str(e)}

    def execute_case_processing(self, case, captcha_input):
        """
        실제 Puppeteer로 사건 처리 실행 함수

        services/puppeteer.py의 PuppeteerService를 사용합니다.

        매개변수:
            case: 사건 정보 딕셔너리 (사건번호, 피고, 법원 등)
            captcha_input: 사용자가 입력한 캡차 텍스트 (6자리 숫자)

        반환값:
            progress_data: 크롤링한 진행내용 데이터 리스트 또는 False (실패 시)
        """
        try:
            case_number = case.get("사건번호", "")

            # WebSocket URL 가져오기 (있으면 재연결)
            browser_ws_url = self.browser_ws_urls.get(case_number)

            # PuppeteerService를 사용하여 사건 처리 실행
            result = self.puppeteer_service.execute_case_processing(
                case, captcha_input, browser_ws_url
            )

            return result

        except Exception as e:
            self.log_message(f"❌ Puppeteer 실행 오류: {case_number} - {e}")
            return False

    def extract_progress_from_result(self, case_number):
        """
        결과 JSON 파일에서 진행내용 데이터 추출

        services/puppeteer.py의 PuppeteerService를 사용합니다.
        """
        return self.puppeteer_service.extract_progress_from_result(case_number)

    def apply_text_colors(self, worksheet, color_info):
        """
        텍스트 색상 적용

        이 메서드는 services/google_sheets.py의 GoogleSheetsService에서 처리됩니다.
        하위 호환성을 위해 유지되지만, 실제로는 사용되지 않습니다.
        """
        # 이 메서드는 더 이상 사용되지 않습니다.
        # GoogleSheetsService.save_progress_data() 내부에서 자동으로 처리됩니다.
        pass

    def load_search_log(self):
        """
        검색 성공 이력 로드 (캡차 입력 성공한 사건번호 목록).
        '기록' 열 표시용. 파일 없으면 빈 리스트.
        """
        path = getattr(config, "SEARCH_LOG_FILE", "search_log.json")
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return (
                        data
                        if isinstance(data, list)
                        else list(data.keys()) if isinstance(data, dict) else []
                    )
            return []
        except Exception as e:
            self.log_message(f"⚠️ 검색 이력 로드 실패: {e}")
            return []

    def add_to_search_log(self, case_number):
        """
        캡차 입력 성공 시 사건번호를 search_log.json에 추가.
        """
        if not case_number:
            return
        path = getattr(config, "SEARCH_LOG_FILE", "search_log.json")
        try:
            log = self.load_search_log()
            if case_number not in log:
                log.append(case_number)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(log, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.log_message(f"⚠️ 검색 이력 저장 실패: {e}")

    def load_update_history(self):
        """
        로컬 업데이트 기록 로드 (services.update_history 사용)
        """
        try:
            return update_history_service.load_update_history(
                config.UPDATE_HISTORY_FILE
            )
        except Exception as e:
            self.log_message(f"⚠️ 업데이트 기록 로드 실패: {e}")
            return {}

    def save_update_history(self, history):
        """
        로컬 업데이트 기록 저장 (services.update_history 사용)
        """
        try:
            update_history_service.save_update_history(
                history, config.UPDATE_HISTORY_FILE
            )
        except Exception as e:
            self.log_message(f"⚠️ 업데이트 기록 저장 실패: {e}")

    def update_case_timestamp(self, case, original_index=None, row_count=0):
        """사건 업데이트 타임스탬프 및 행 개수 기록, GUI 갱신 (기록은 services.update_history 사용)"""
        try:
            history = self.load_update_history()
            case_number = case.get("사건번호", "")

            # 이전 행 개수 가져오기 (기록 저장 전)
            old_data = history.get(case_number, {})
            if isinstance(old_data, str):
                old_row_count = 0
            else:
                old_row_count = old_data.get("row_count", 0)

            # 서비스로 기록 갱신 후 저장
            new_history = update_history_service.update_case_record(
                case_number, row_count, history
            )
            self.save_update_history(new_history)
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # 새로 추가된 행 개수 계산
            new_rows = row_count - old_row_count if row_count > old_row_count else 0

            self.log_message(
                f"📝 업데이트 기록: {case_number} - {current_time} (행: {row_count}, 신규: +{new_rows})"
            )

            # GUI 업데이트 (날짜 + D+0 + 새 행 개수 표시)
            if original_index is not None:
                date_str = current_time.split(" ")[0]  # 날짜만 추출
                new_rows_text = f" (+{new_rows})" if new_rows > 0 else ""

                def update_labels():
                    # D+n 라벨 업데이트
                    if original_index in self.case_update_labels:
                        display_text = f"D+0{new_rows_text}"
                        color = "#28A745" if new_rows > 0 else "#0D6EFD"
                        self.case_update_labels[original_index].configure(
                            text=display_text, text_color=color
                        )

                    # 날짜 라벨 업데이트 또는 생성
                    if original_index in self.case_update_date_labels:
                        if self.case_update_date_labels[original_index]:
                            self.case_update_date_labels[original_index].configure(
                                text=date_str
                            )
                        else:
                            # 날짜 라벨이 없으면 생성
                            if original_index in self.case_update_labels:
                                parent = self.case_update_labels[original_index].master
                                try:
                                    parent_fg = (
                                        parent.cget("fg_color")
                                        if hasattr(parent, "cget")
                                        else "#2B2B2B"
                                    )
                                except Exception:
                                    parent_fg = "#2B2B2B"
                                new_date_label = ctk.CTkLabel(
                                    parent,
                                    text=date_str,
                                    font=ctk.CTkFont(family="맑은 고딕", size=12),
                                    text_color="#6C757D",
                                )
                                new_date_label.pack(
                                    before=self.case_update_labels[original_index]
                                )
                                self.case_update_date_labels[original_index] = (
                                    new_date_label
                                )

                self.root.after(0, update_labels)

        except Exception as e:
            self.log_message(f"⚠️ 업데이트 기록 실패: {e}")

    def get_days_since_update(self, case):
        """최근 업데이트 이후 경과일수 조회 (정수 반환, 없으면 -1). services.update_history 사용."""
        history = self.load_update_history()
        return update_history_service.get_days_since_update(case, history)

    def load_status_history(self):
        """
        상태 열 영구 보존용 JSON 로드.
        반환: { 사건번호: {"status": str, "color": str, "emoji": str}, ... }
        """
        path = getattr(config, "STATUS_HISTORY_FILE", "status_history.json")
        try:
            if os.path.isfile(path):
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return {}

    def load_column_widths(self):
        """
        저장된 열 너비 JSON 로드.
        리스트 길이가 COL_WIDTHS와 같을 때만 반환, 아니면 None.
        """
        path = getattr(config, "COLUMN_WIDTHS_FILE", "column_widths.json")
        try:
            if os.path.isfile(path):
                with open(path, "r", encoding="utf-8") as f:
                    widths = json.load(f)
                if isinstance(widths, list) and len(widths) == len(COL_WIDTHS):
                    return widths
        except Exception:
            pass
        return None

    def load_column_order(self):
        """
        저장된 열 순서 JSON 로드.
        리스트 길이가 COL_NAMES와 같고, 0~9 인덱스가 각 한 번씩만 있으면 반환, 아니면 None.
        """
        path = getattr(config, "COLUMN_ORDER_FILE", "column_order.json")
        try:
            if os.path.isfile(path):
                with open(path, "r", encoding="utf-8") as f:
                    order = json.load(f)
                if (
                    isinstance(order, list)
                    and len(order) == len(COL_NAMES)
                    and set(order) == set(range(len(COL_NAMES)))
                ):
                    return order
        except Exception:
            pass
        return None

    def _save_column_order(self):
        """현재 열 순서를 COLUMN_ORDER_FILE에 JSON 배열로 저장."""
        path = getattr(config, "COLUMN_ORDER_FILE", "column_order.json")
        try:
            if hasattr(self, "col_order") and self.col_order:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(self.col_order, f, indent=2)
        except Exception:
            pass

    def _save_column_widths(self):
        """현재 열 너비를 COLUMN_WIDTHS_FILE에 JSON 배열로 저장."""
        path = getattr(config, "COLUMN_WIDTHS_FILE", "column_widths.json")
        try:
            if hasattr(self, "col_widths") and self.col_widths:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(self.col_widths, f, indent=2)
        except Exception:
            pass

    def save_status_history(self, case_number, status, color, emoji=""):
        """
        상태 변경 시 JSON에 기록 (직전 상태 유지: 완료/저장 실패 등).
        """
        path = getattr(config, "STATUS_HISTORY_FILE", "status_history.json")
        try:
            history = self.load_status_history()
            history[case_number] = {"status": status, "color": color, "emoji": emoji}
            with open(path, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.log_message(f"⚠️ 상태 기록 저장 실패: {e}")

    def format_update_timestamp_rows(self, worksheet, start_row):
        """
        업데이트 일시 행 포맷팅 (좌측 정렬)

        이 메서드는 services/google_sheets.py의 GoogleSheetsService에서 처리됩니다.
        하위 호환성을 위해 유지되지만, 실제로는 사용되지 않습니다.
        """
        # 이 메서드는 더 이상 사용되지 않습니다.
        # GoogleSheetsService.save_progress_data() 내부에서 자동으로 처리됩니다.
        pass

    def auto_resize_columns(self, worksheet):
        """
        열 너비 자동 조정

        이 메서드는 services/google_sheets.py의 GoogleSheetsService에서 처리됩니다.
        하위 호환성을 위해 유지되지만, 실제로는 사용되지 않습니다.
        """
        # 이 메서드는 더 이상 사용되지 않습니다.
        # GoogleSheetsService.save_progress_data() 내부에서 자동으로 처리됩니다.
        pass

    @staticmethod
    def _normalize_text(text):
        """비교용: 모든 공백(스페이스/탭/줄바꿈) 제거하여 미세 차이로 인한 중복 오판 방지."""
        if text is None:
            return ""
        return "".join(str(text).split())

    def filter_new_data(self, scraped_data, last_entry):
        """
        크롤링된 전체 데이터에서 last_entry 이후의 신규 데이터만 반환.
        last_entry가 없거나 일치하는 항목이 없으면 전체 데이터 반환.
        비교 시 공백 정규화를 적용하여 중복 저장을 방지합니다.
        """
        if (
            not last_entry
            or not isinstance(scraped_data, list)
            or len(scraped_data) == 0
        ):
            return scraped_data if isinstance(scraped_data, list) else []
        le_date = self._normalize_text(last_entry.get("date", ""))
        le_content = self._normalize_text(last_entry.get("content", ""))
        for i, row in enumerate(scraped_data):
            if not isinstance(row, dict):
                continue
            if (
                self._normalize_text(row.get("date", "")) == le_date
                and self._normalize_text(row.get("content", "")) == le_content
            ):
                return scraped_data[i + 1 :]
        return scraped_data

    def save_to_google_sheets(self, case, result_data):
        """
        구글 시트에 결과를 저장하는 함수

        services/google_sheets.py의 GoogleSheetsService를 사용합니다.

        매개변수:
            case: 사건 정보 딕셔너리 (사건번호, 피고, 법원, 비고 등)
            result_data: 크롤링한 진행내용 데이터 리스트
                예: [
                    {'date': '2024-01-01', 'content': '...', 'result': '...', 'document': '...'},
                    ...
                ]

        반환값:
            저장된 행 개수 (int) 또는 False (실패 시)
        """
        # GoogleSheetsService를 사용하여 저장
        return self.google_sheets_service.save_progress_data(
            case, result_data, log_callback=self.log_message
        )

    def update_case_status(self, case_index, status, color, emoji=""):
        """사건 상태 업데이트 (이모지 포함) (Thread-Safe). 상태 열 영구 보존용 JSON에도 기록."""

        def _update():
            if case_index in self.case_status:
                display_text = f"{emoji} {status}" if emoji else status
                self.case_status[case_index].configure(
                    text=display_text, text_color=color
                )
                # 직전 상태 기록 (저장 실패/완료 등 유지)
                if 0 <= case_index < len(self.case_list):
                    case_number = self.case_list[case_index].get("사건번호", "")
                    if case_number:
                        self.save_status_history(case_number, status, color, emoji)

                if case_index in self.case_frames:
                    if status.startswith("처리중"):
                        self.case_frames[case_index].configure(fg_color="#FFF3CD")
                        for widget in self.case_frames[case_index].winfo_children():
                            try:
                                widget.configure(fg_color="#FFF3CD")
                            except (tk.TclError, AttributeError):
                                try:
                                    widget.config(bg="#FFF3CD")
                                except Exception:
                                    pass
                    elif status.startswith("완료"):
                        self.case_frames[case_index].configure(fg_color="#D4EDDA")
                        for widget in self.case_frames[case_index].winfo_children():
                            try:
                                widget.configure(fg_color="#D4EDDA")
                            except (tk.TclError, AttributeError):
                                try:
                                    widget.config(bg="#D4EDDA")
                                except Exception:
                                    pass
                    elif status.startswith("실패") or status.startswith("오류"):
                        self.case_frames[case_index].configure(fg_color="#F8D7DA")
                        for widget in self.case_frames[case_index].winfo_children():
                            try:
                                widget.configure(fg_color="#F8D7DA")
                            except (tk.TclError, AttributeError):
                                try:
                                    widget.config(bg="#F8D7DA")
                                except Exception:
                                    pass

        # 메인 스레드에서 실행
        self.root.after(0, _update)

    def update_captcha_image(self, case_index, image_path):
        """
        캡차 이미지 업데이트 (Thread-Safe)

        스레드에서 호출될 수 있으므로 root.after()를 사용하여 메인 스레드에서 실행합니다.
        """
        # 인덱스 유효성 검사
        if case_index not in self.case_images:
            self.log_message(f"❌ 캡차 이미지 업데이트 실패: 인덱스 {case_index} 없음")
            self.log_message(
                f"🔍 [DEBUG] 사용 가능한 인덱스: {sorted(self.case_images.keys())}"
            )
            return False

        # image_path와 case_index를 클로저로 캡처 (비동기 실행을 위해)
        # 각 업데이트에 인덱스 기반 고정 지연 시간을 부여하여 순차 실행 보장
        # 인덱스가 클수록 더 늦게 실행되도록 (각 인덱스마다 100ms씩 지연)
        delay_ms = case_index * 100  # 인덱스 0: 0ms, 인덱스 1: 100ms, 인덱스 10: 1000ms

        # Thread-Safe: 메인 스레드에서 실행
        def _update():
            try:
                # 다시 한번 인덱스 확인 (안전장치)
                if case_index not in self.case_images:
                    self.log_message(
                        f"❌ [ERROR] _update() 실행 시 인덱스 {case_index} 없음"
                    )
                    return

                image_label = self.case_images[case_index]

                if image_path == "__CLICK__":
                    image_label.config(
                        image="",
                        text="최근검색 (자동클릭)",
                        fg="blue",
                        font=("맑은 고딕", 10, "bold"),
                    )
                    if case_index in self.case_image_photos:
                        del self.case_image_photos[case_index]
                    self.log_message(
                        f"⚡ [DEBUG] 캡차 스킵 모드 표시: 인덱스 {case_index}"
                    )
                    return

                if image_path and os.path.exists(image_path):
                    # 파일 크기 확인
                    file_size = os.path.getsize(image_path)
                    self.log_message(
                        f"🔍 [DEBUG] 이미지 파일 확인: 인덱스 {case_index}, 경로: {image_path} ({file_size} bytes)"
                    )

                    from PIL import Image, ImageTk

                    # 이미지 로드 및 리사이즈 (적절한 크기)
                    img = Image.open(image_path)
                    img = img.resize(
                        (200, 60), Image.Resampling.LANCZOS
                    )  # 적절한 크기로 조정
                    photo = ImageTk.PhotoImage(img)

                    # 이미지 참조를 인스턴스 변수에 저장 (가비지 컬렉션 방지)
                    self.case_image_photos[case_index] = photo

                    # 이미지 표시 (적절한 크기)
                    image_label.config(image=photo, text="", width=200, height=60)
                    image_label.image = photo  # 참조 유지 (중요: 가비지 컬렉션 방지)

                    # GUI 강제 업데이트
                    self.root.update_idletasks()

                    self.log_message(
                        f"🖼️ [DEBUG] 캡차 이미지 업데이트 성공: 인덱스 {case_index}, 사건번호: {self.case_list[case_index].get('사건번호', '') if case_index < len(self.case_list) else 'N/A'}"
                    )
                    self.log_message(f"✅ GUI에 캡차 이미지 표시 완료: {image_path}")

                else:
                    self.log_message(f"⚠️ 캡차 이미지 없음: {image_path}")
                    image_label.config(image="", text="이미지없음", fg="red")
                    # 참조 제거
                    if case_index in self.case_image_photos:
                        del self.case_image_photos[case_index]

            except Exception as e:
                self.log_message(f"❌ 이미지 업데이트 오류: {e}")
                import traceback

                self.log_message(f"❌ [DEBUG] 스택 트레이스: {traceback.format_exc()}")
                if case_index in self.case_images:
                    try:
                        self.case_images[case_index].config(
                            image="", text="오류", fg="red"
                        )
                    except:
                        pass

        # 메인 스레드에서 실행 (Thread-Safe) - 지연 시간을 두어 순차 실행 보장
        self.root.after(delay_ms, _update)
        return True  # 비동기 실행이므로 True 반환

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
            if case.get("사건번호", "") == case_number:
                return i
        return -1

    def processing_completed(self):
        """처리 완료 후 UI 업데이트"""
        self._set_control_btn_state(self.start_btn, True)
        self._set_control_btn_state(self.stop_btn, False)
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
                self.progress_var.set(percentage)
                if hasattr(self, "progress_bar") and self.progress_bar.winfo_exists():
                    self.progress_bar.set(percentage / 100.0)

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
        self.root.after(100, self.load_google_sheet)
        self.root.mainloop()

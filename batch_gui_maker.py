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

# queue: 메인 스레드 UI 업데이트를 위한 스레드 안전 큐
import queue

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
from services.process_controller import ProcessController
from services.history_manager import HistoryManager
from services.logger_service import setup_logger, register_gui_handler, get_logger

# services.update_history: 업데이트 기록 파일 읽기/쓰기
from services import update_history as update_history_service

# utils.email_manager: 알림메일 미발송 내역 누적
from utils import email_manager as email_manager_module

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
# 설정 편집 다이얼로그 (user_settings.json GUI)
from gui.dialogs.settings_dialog import SettingsDialog
# UI 패널 모듈 (헤더, 제어, 설정, 사건 목록, 진행상황) - 유지보수용 분리
from gui.panels import (
    HeaderPanel,
    ControlPanel,
    SettingsPanel,
    ProgressPanel,
    CaseListPanel,
)

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

        # UI 업데이트 관련 상태 관리
        self._ui_updating = False
        self._extra_width_last_col = 0
        
        # UI 업데이트 메시지 큐 (메인 스레드 응답 없음 방지용)
        self.ui_queue = queue.Queue()
        
        # 파일 I/O 동시 접근 방지용 Lock (status_history 등)
        self._file_lock = threading.Lock()

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
        # 찾기(검색) 상태: 크롬 스타일 이전/다음 순환용
        self._last_search_query = ""
        self._current_search_index = 0

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
        # 로거 초기화 (파일 핸들러; GUI 핸들러는 create_progress_panel 후 등록)
        # ============================================================
        setup_logger()

        # ============================================================
        # 서비스 객체 생성
        # ============================================================
        self.google_sheets_service = GoogleSheetsService()
        # processing_flag는 나중에 설정 (self.processing이 아직 생성되지 않았음)
        self.puppeteer_service = PuppeteerService()
        # 증분 업데이트용 마지막 저장 항목 (ProcessController에서 get_last_entry/update_last_entry 사용)
        self.history_manager = update_history_service.HistoryManager()
        # 검색 로그·상태 히스토리 파일 I/O (load_search_log, save_status_history 등)
        self.log_history_manager = HistoryManager(self)
        # 사건번호별 고정 프로필(인스턴스) 사용 시 동일 프로필 동시 접근 방지
        max_profiles = getattr(config, "MAX_PARALLEL_LIMIT", 20)
        self.profile_locks = [threading.Lock() for _ in range(max_profiles)]

        # 사건 조회/캡차 처리 오케스트레이션 (스레드·병렬·재시도 로직은 ProcessController에서 담당)
        self.process_controller = ProcessController(self)

        return self.root

    def create_header(self, parent):
        """헤더 영역 생성. gui.panels.HeaderPanel에 위임."""
        return HeaderPanel.create(parent, self)

    def create_control_panel(self, parent):
        """제어 패널 생성. gui.panels.ControlPanel에 위임."""
        frame = ControlPanel.create(parent, self)
        self.root.after(100, self.update_email_btn_text)
        return frame

    def _set_control_btn_state(self, btn, enabled):
        """제어 패널 버튼 활성/비활성 + 회색 스타일 적용. gui.panels.ControlPanel에 위임."""
        ControlPanel.set_control_btn_state(self, btn, enabled)

    def _open_settings_dialog(self):
        """설정(Config) 편집 다이얼로그를 엽니다. 저장 시 config가 갱신되며, 일부 항목은 재시작 후 적용됩니다."""
        dlg = SettingsDialog(
            self.root,
            on_save_callback=lambda: self.log_message("설정이 저장되었습니다. 일부 항목은 다음 작업부터 적용됩니다."),
        )
        dlg.focus_set()

    def create_settings_panel(self, parent):
        """설정 패널 생성. gui.panels.SettingsPanel에 위임."""
        return SettingsPanel.create(parent, self)

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
        """사건 목록 패널 생성. gui.panels.CaseListPanel에 위임."""
        return CaseListPanel.create(parent, self)

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

    def update_search_count(self):
        """검색창 타이핑 시 매치 개수 라벨 갱신 (0/N)."""
        if not hasattr(self, "search_count_label") or not self.search_count_label.winfo_exists():
            return
        if not hasattr(self, "search_entry") or not self.search_entry.winfo_exists():
            return
        query = self.search_entry.get().strip()
        if not query:
            self.search_count_label.configure(text="0/0")
            return
        match_indices = self._find_match_indices(query)
        n = len(match_indices)
        self.search_count_label.configure(text=f"0/{n}" if n > 0 else "0/0")

    def perform_search(self, query=None, direction="next"):
        """상단 검색창 또는 팝업에서 호출. direction: 'next' 다음, 'prev' 이전. query가 None이면 search_entry에서 가져옴."""
        if query is None and hasattr(self, "search_entry") and self.search_entry.winfo_exists():
            query = self.search_entry.get().strip()
        if not query:
            return
        match_indices = self._find_match_indices(query)
        if not match_indices:
            messagebox.showinfo("찾기", "검색어와 일치하는 항목이 없습니다.")
            if hasattr(self, "search_count_label") and self.search_count_label.winfo_exists():
                self.search_count_label.configure(text="0/0")
            return
        n = len(match_indices)
        query_changed = getattr(self, "_last_search_query", "") != query
        if query_changed:
            self._last_search_query = query
            self._current_search_index = 0
        else:
            if direction == "next":
                self._current_search_index = (self._current_search_index + 1) % n
            else:
                self._current_search_index = (self._current_search_index - 1 + n) % n
        idx = self._current_search_index
        row_index = match_indices[idx]
        self._scroll_to_row_and_highlight(row_index, query)
        if hasattr(self, "search_count_label") and self.search_count_label.winfo_exists():
            self.search_count_label.configure(text=f"{idx + 1}/{n}")

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
        """진행상황 패널 생성. gui.panels.ProgressPanel에 위임. 생성 후 GUI 로그 핸들러 등록."""
        frame = ProgressPanel.create(parent, self)
        register_gui_handler(self)
        return frame

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
        """구글 시트에서 사건 목록 로드 (비동기). UI 프리징 방지를 위해 백그라운드 스레드에서 데이터를 가져옵니다."""
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

        # 로딩 중 버튼 비활성화 및 문구 변경 (중복 클릭·UI 혼선 방지, 사용자 피드백)
        if hasattr(self, "refresh_btn") and self.refresh_btn.winfo_exists():
            self.refresh_btn.configure(text="⏳ 로딩 중...")
            self._set_control_btn_state(self.refresh_btn, False)
        self._set_control_btn_state(self.start_btn, False)
        self.log_message("구글 시트 연결 중...")

        def worker():
            try:
                google_data, spreadsheet = load_google_sheet_data()
                self.root.after(0, lambda: self._on_load_google_sheet_done(google_data, spreadsheet, None))
            except Exception as e:
                self.root.after(0, lambda: self._on_load_google_sheet_done(None, None, e))

        threading.Thread(target=worker, daemon=True).start()

    def _on_load_google_sheet_done(self, google_data, spreadsheet, error):
        """비동기 로드 완료 시 메인 스레드에서 호출. UI 갱신 및 버튼 복원."""
        # 버튼 항상 복원 (새로고침 문구 복구)
        if hasattr(self, "refresh_btn") and self.refresh_btn.winfo_exists():
            self.refresh_btn.configure(text="🔄 새로고침")
            self._set_control_btn_state(self.refresh_btn, True)
        self.start_btn.configure(text="🖼️ 사건 조회 로드 실행\n(캡차 로드 실행)")
        self._set_control_btn_state(self.start_btn, True)

        if error:
            self.log_message(f"❌ 구글 시트 로드 실패: {error}")
            messagebox.showerror("오류", f"구글 시트 로드 실패: {error}")
            return

        if not google_data:
            self.log_message("구글 시트 데이터를 로드할 수 없습니다.")
            messagebox.showerror("오류", "구글 시트 데이터를 로드할 수 없습니다.")
            return

        self.case_list = google_data
        self.sort_case_list()

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
        self.update_case_list_ui()

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
        """사건 목록 헤더 생성 (col_order 순서대로 표시). CaseListPanel에 위임."""
        CaseListPanel.create_list_header(self)

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
        """단일 사건 행 위젯 생성. CaseListPanel에 위임. (row_container, components, cell_frames) 반환."""
        return CaseListPanel.create_case_row(
            self, parent, case, index, total_width, initial_status
        )

    def _validate_captcha_entry(self, index):
        """캡차 입력 6자리 숫자만 허용 (CTkEntry용)."""
        if index not in self.case_inputs:
            return
        val = self.case_inputs[index].get()
        cleaned = "".join(c for c in val if c.isdigit())[:6]
        if cleaned != val:
            self.case_inputs[index].set(cleaned)

    def update_case_list_ui(self):
        """사건 목록 UI 업데이트 (비동기 배치 처리로 UI 프리징 방지)"""
        if getattr(self, "_ui_updating", False):
            self.log_message("⚠️ UI 업데이트가 이미 진행 중입니다. 대기합니다.")
            return
        
        try:
            self._ui_updating = True
            n = len(self.case_list) if self.case_list else 0
            if hasattr(self, "case_list_title_label") and self.case_list_title_label.winfo_exists():
                self.case_list_title_label.configure(text=f"📋 사건 목록({n}) (로딩 중...)")
            self.log_message(f"🔄 [DEBUG] UI 업데이트 시작: {n}건 (배치 처리)")

            # 기존 위젯 제거 (메인 스레드에서 즉시 실행)
            for widget in self.case_list_frame.winfo_children():
                widget.destroy()

            # 상태 데이터 초기화
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

            # 컬럼 설정 및 너비 계산
            loaded_widths = self.load_column_widths()
            if loaded_widths is not None and len(loaded_widths) == len(COL_WIDTHS):
                self.col_widths = list(loaded_widths)
            elif not hasattr(self, "col_widths") or len(self.col_widths) != len(COL_WIDTHS):
                self.col_widths = list(COL_WIDTHS)

            order_loaded = self.load_column_order()
            if order_loaded is not None and len(order_loaded) == len(COL_NAMES):
                self.col_order = list(order_loaded)
            elif not hasattr(self, "col_order") or len(self.col_order) != len(COL_NAMES):
                self.col_order = list(DEFAULT_COL_ORDER)

            effective_total, extra_last = self._get_effective_widths()
            self._extra_width_last_col = extra_last
            
            if hasattr(self, "header_container") and self.header_container.winfo_exists():
                self.header_container.configure(width=effective_total)
            if hasattr(self, "header_canvas") and self.header_canvas.winfo_exists():
                self.header_canvas.configure(scrollregion=(0, 0, effective_total, 40))
            if hasattr(self, "case_list_frame") and self.case_list_frame.winfo_exists():
                self.case_list_frame.configure(width=effective_total)

            # 헤더 생성
            self.create_list_header()
            
            # 저장된 직전 상태 로드
            status_history = self.load_status_history()
            
            # 배치 생성을 위한 변수
            batch_size = 5  # 한 번에 생성할 행 수 (작을수록 UI 응답성 향상)
            
            def process_batch(start_idx):
                if not self.root.winfo_exists():
                    self._ui_updating = False
                    return
                    
                end_idx = min(start_idx + batch_size, len(self.case_list))
                for i in range(start_idx, end_idx):
                    case = self.case_list[i]
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

                # 스크롤 영역 실시간 업데이트
                self.case_list_frame.update_idletasks()
                self.case_canvas.configure(scrollregion=self.case_canvas.bbox("all"))
                
                if end_idx < len(self.case_list):
                    # 다음 배치 예약
                    self.root.after(1, lambda: process_batch(end_idx))
                else:
                    # 모든 배치 완료
                    self._on_ui_update_complete()

            # 첫 번째 배치 시작
            if self.case_list:
                process_batch(0)
            else:
                self._on_ui_update_complete()
                
        except Exception as e:
            self.log_message(f"❌ UI 업데이트 중 오류 발생: {e}")
            self._ui_updating = False

    def _on_ui_update_complete(self):
        """UI 업데이트 완료 후 마무리 작업"""
        try:
            n = len(self.case_list) if self.case_list else 0
            if hasattr(self, "case_list_title_label") and self.case_list_title_label.winfo_exists():
                self.case_list_title_label.configure(text=f"📋 사건 목록({n})")
            
            # 헤더 토글 상태 맞춤
            if self.case_checkboxes:
                selected_count = sum(1 for v in self.case_checkboxes.values() if v.get())
                self.header_select_all_var.set(selected_count == len(self.case_checkboxes))
                
            self.log_message(f"✅ UI 업데이트 완료: {n}건")
            
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
        finally:
            self._ui_updating = False

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
        """캡차 이미지 로드 시작. 선택 사건 검증·스레드 기동은 ProcessController에 위임."""
        selected_cases_with_index = self.get_selected_cases()
        selected_cases = [case for _, case in selected_cases_with_index]
        self.process_controller.start_processing(selected_cases)

    def stop_batch_processing(self):
        """일괄 처리 중지. ProcessController에 위임."""
        self.process_controller.stop_processing()

    def cleanup_case_process(self, case_number):
        """개별 사건의 브라우저 프로세스 정리. ProcessController에 위임."""
        self.process_controller.cleanup_case_process(case_number)

    def _lane_for_case(self, case_number, n_lanes):
        """전용 차로: 사건번호 기준 고정 레인. ProcessController에 위임."""
        return self.process_controller._lane_for_case(case_number, n_lanes)

    def get_case_profile_index(self, case_number):
        """사건번호별 고정 프로필 인덱스. ProcessController에 위임."""
        return self.process_controller.get_case_profile_index(case_number)

    def execute_actual_processing(self, cases):
        """실제 처리 실행 (전용 차로제). ProcessController에 위임."""
        self.process_controller.execute_actual_processing(cases)

    def _check_and_prompt_failed_cases(self, processed_cases):
        """실패한 사건 재실행 여부 알림. ProcessController에 위임."""
        self.process_controller._check_and_prompt_failed_cases(processed_cases)

    def _process_auto_case(self, case, case_index):
        """자동 클릭 케이스 즉시 처리. ProcessController에 위임."""
        return self.process_controller._process_auto_case(case, case_index)

    def process_single_case_parallel(self, case, case_index, instance_index=0):
        """병렬 처리용 단일 사건. ProcessController에 위임."""
        return self.process_controller.process_single_case_parallel(case, case_index, instance_index)

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
        """캡차 검증·실행·저장. ProcessController에 위임. 반환: (completed_delta, failed_delta)."""
        return self.process_controller._process_one_case(
            original_index, case, total_cases, total_start_time, selected_cases
        )

    def process_all_captcha_inputs(self):
        """모든 캡차 입력 처리. ProcessController에 위임 (캡차 입력 완료 버튼 → 백그라운드 스레드)."""
        self.process_controller.process_all_captcha_inputs()

    def capture_captcha_image(self, case_number, defendant, court, instance_index=0):
        """캡차 이미지 캡처. ProcessController에 위임."""
        return self.process_controller.capture_captcha_image(
            case_number, defendant, court, instance_index
        )

    def execute_case_processing_with_captcha(self, case, case_index, instance_index=0):
        """캡차 이미지 캡처 후 GUI 표시. ProcessController에 위임."""
        return self.process_controller.execute_case_processing_with_captcha(
            case, case_index, instance_index
        )

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
        """Puppeteer로 사건 처리 실행. ProcessController에 위임."""
        return self.process_controller.execute_case_processing(case, captcha_input)

    def extract_progress_from_result(self, case_number):
        """
        결과 JSON 파일에서 진행내용 데이터 추출

        services/puppeteer.py의 PuppeteerService를 사용합니다.
        """
        return self.puppeteer_service.extract_progress_from_result(case_number)

    def load_search_log(self):
        """검색 성공 이력 로드. log_history_manager에 위임."""
        return self.log_history_manager.load_search_log()

    def add_to_search_log(self, case_number):
        """검색 성공 시 사건번호를 search_log에 추가. log_history_manager에 위임."""
        self.log_history_manager.add_to_search_log(case_number)

    def load_update_history(self):
        """
        로컬 업데이트 기록 로드 (services.update_history 사용)
        """
        try:
            with getattr(self, "_file_lock", threading.Lock()):
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
            with getattr(self, "_file_lock", threading.Lock()):
                update_history_service.save_update_history(
                    history, config.UPDATE_HISTORY_FILE
                )
        except Exception as e:
            self.log_message(f"⚠️ 업데이트 기록 저장 실패: {e}")

    def update_case_timestamp(self, case, original_index=None, row_count=0):
        """사건 업데이트 타임스탬프 및 행 개수 기록, GUI 갱신 (기록은 services.update_history 사용)"""
        try:
            case_number = case.get("사건번호", "")
            
            # _file_lock을 사용하여 로드-수정-저장을 원자적으로 처리
            with getattr(self, "_file_lock", threading.Lock()):
                # 최신 상태 다시 읽기
                history = update_history_service.load_update_history(config.UPDATE_HISTORY_FILE)
                
                # 이전 행 개수 가져오기
                old_data = history.get(case_number, {})
                if isinstance(old_data, str):
                    old_row_count = 0
                else:
                    old_row_count = old_data.get("row_count", 0)

                # 기록 갱신 후 저장
                new_history = update_history_service.update_case_record(
                    case_number, row_count, history
                )
                update_history_service.save_update_history(
                    new_history, config.UPDATE_HISTORY_FILE
                )
                
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
        """상태 열 영구 보존용 JSON 로드. log_history_manager에 위임."""
        return self.log_history_manager.load_status_history()

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
            with getattr(self, "_file_lock", threading.Lock()):
                if hasattr(self, "col_order") and self.col_order:
                    with open(path, "w", encoding="utf-8") as f:
                        json.dump(self.col_order, f, indent=2)
        except Exception:
            pass

    def _save_column_widths(self):
        """현재 열 너비를 COLUMN_WIDTHS_FILE에 JSON 배열로 저장."""
        path = getattr(config, "COLUMN_WIDTHS_FILE", "column_widths.json")
        try:
            with getattr(self, "_file_lock", threading.Lock()):
                if hasattr(self, "col_widths") and self.col_widths:
                    with open(path, "w", encoding="utf-8") as f:
                        json.dump(self.col_widths, f, indent=2)
        except Exception:
            pass

    def save_status_history(self, case_number, status, color, emoji=""):
        """상태 변경 시 JSON에 기록. log_history_manager에 위임."""
        self.log_history_manager.save_status_history(case_number, status, color, emoji)

    def filter_new_data(self, scraped_data, last_entry):
        """last_entry 이후 신규 데이터만 반환. ProcessController에 위임."""
        return self.process_controller.filter_new_data(scraped_data, last_entry)

    def save_to_google_sheets(self, case, result_data):
        """구글 시트에 진행내용 저장. ProcessController에 위임."""
        return self.process_controller.save_to_google_sheets(case, result_data)

    def update_case_status(self, case_index, status, color, emoji=""):
        """사건 상태 업데이트 (이모지 포함) (Thread-Safe). 큐를 통해 메인 스레드에서 처리됩니다."""

        # 직전 상태 기록 (저장 실패/완료 등 유지) - 메인 UI 스레드 밖에서 실행 (파일 I/O)
        if 0 <= case_index < len(self.case_list):
            case_number = self.case_list[case_index].get("사건번호", "")
            if case_number:
                # 별도 스레드에서 파일 저장을 수행하여 UI 프리징 방지
                threading.Thread(target=self.save_status_history, args=(case_number, status, color, emoji), daemon=True).start()

        # UI 업데이트용 데이터 준비
        display_text = f"{emoji} {status}" if emoji else status
        
        bg_color = None
        if status.startswith("처리중"):
            bg_color = "#FFF3CD"
        elif status.startswith("완료"):
            bg_color = "#D4EDDA"
        elif status.startswith("실패") or status.startswith("오류"):
            bg_color = "#F8D7DA"
            
        # 큐에 메시지 넣기
        self.ui_queue.put(("status", (case_index, display_text, color, bg_color), {}))

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

    def update_email_btn_text(self):
        """알림메일 버튼의 텍스트 및 활성/비활성 색상을 갱신합니다. 보낼 내역 또는 마지막 조회 결과가 있으면 활성."""
        btn = getattr(self, "email_btn", None)
        if not btn or not btn.winfo_exists():
            return
        summary_text, last_sent = email_manager_module.get_summary_text()
        has_content = bool(summary_text and summary_text.strip()) or email_manager_module.has_last_run_result()
        ControlPanel.set_control_btn_state(self, btn, has_content)
        if not last_sent:
            last_sent = "없음"
        btn.configure(text=f"📧 모든 사건 메일 발송 (최근: {last_sent})", height=ControlPanel.BTN_H)

    def send_notification_email(self):
        """미발송 누적 내역 또는 마지막 조회 결과를 구글 시트 '알림메일' 시트에 기록하고, 로컬 누적을 비웁니다. (비동기 처리)"""
        summary_html, last_sent = email_manager_module.get_summary_html()
        if not summary_html or not summary_html.strip():
            messagebox.showinfo("알림메일", "보낼 내역이 없습니다. (조회를 실행한 뒤 메일을 보낼 수 있습니다.)")
            return
            
        recipient = (getattr(config, "NOTIFICATION_EMAIL_ADDRESS", "") or "").strip()
        if not recipient:
            messagebox.showwarning("알림메일", "설정에서 알림 수신 메일 주소를 먼저 입력해주세요.")
            return

        # 버튼 비활성화 (중복 클릭 방지)
        btn = getattr(self, "email_btn", None)
        if btn and btn.winfo_exists():
            self._set_control_btn_state(btn, False)
            btn.configure(text="⏳ 기록 및 발송 중...")

        def worker():
            try:
                # 1. 구글 시트 기록 (네트워크 작업)
                ok = self.google_sheets_service.append_notification_mail(summary_html, recipient)
                if not ok:
                    self.root.after(0, lambda: messagebox.showerror("알림메일", "구글 시트에 기록하는 데 실패했습니다."))
                    return
                
                # 2. 로컬 데이터 비우기
                email_manager_module.clear_unsent_emails_and_update_last_sent()
                
                # 3. 즉시 발송 요청 (웹 앱 URL이 있는 경우)
                msg_suffix = ""
                webapp_url = (getattr(config, "NOTIFICATION_GAS_WEBAPP_URL", "") or "").strip()
                if webapp_url:
                    try:
                        import urllib.request
                        req = urllib.request.Request(webapp_url, method="POST", data=b"")
                        with urllib.request.urlopen(req, timeout=15) as _:
                            msg_suffix = "\n\n(웹 앱을 통해 즉시 발송을 요청했습니다.)"
                    except Exception as e:
                        self.log_message(f"⚠️ GAS 웹 앱 즉시 발송 호출 실패: {e}")
                        msg_suffix = "\n\n(웹 앱 호출에 실패했습니다. 트리거가 설정되어 있다면 1분 내로 발송됩니다.)"

                # 4. 완료 후 UI 업데이트
                def final_update():
                    self.update_email_btn_text()
                    messagebox.showinfo("알림메일", f"알림메일 시트에 기록했습니다. (발송상태: 대기){msg_suffix}")
                
                self.root.after(0, final_update)
                
            except Exception as e:
                self.log_message(f"❌ 알림메일 기록 실패: {e}")
                self.root.after(0, lambda: messagebox.showerror("알림메일", f"기록 중 오류가 발생했습니다: {e}"))
            finally:
                # 버튼 상태 복원
                if btn and btn.winfo_exists():
                    self.root.after(0, lambda: self._set_control_btn_state(btn, True))
                    self.root.after(0, self.update_email_btn_text)

        threading.Thread(target=worker, daemon=True).start()

    def processing_completed(self):
        """처리 완료 후 UI 업데이트"""
        self._set_control_btn_state(self.start_btn, True)
        self._set_control_btn_state(self.stop_btn, False)
        self.log_message("🎉 모든 사건 처리 완료!")
        messagebox.showinfo("완료", "모든 사건 처리가 완료되었습니다.")

    def log_message(self, message):
        """로그 메시지 추가 (표준 로거로 전달 → 파일 + GUI 핸들러)"""
        get_logger().info("%s", message)

    def update_progress(self, percentage, status_text=""):
        """진행률 업데이트 (Thread-Safe). 큐를 통해 메인 스레드에서 처리됩니다."""
        self.ui_queue.put(("progress", (percentage, status_text), {}))

    def _process_ui_queue(self):
        """
        메인 스레드에서 주기적으로 호출되어 UI 업데이트 큐를 처리합니다.
        여러 스레드에서 요청한 UI 변경 사항을 한 번에 모아서 처리하여 병목을 방지합니다.
        """
        try:
            # 큐에 쌓인 메시지를 최대 100개까지만 한 번에 처리하여 메인 스레드 블로킹 방지
            for _ in range(100):
                if self.ui_queue.empty():
                    break
                task, args, kwargs = self.ui_queue.get_nowait()
                
                try:
                    if task == "log":
                        # 로그 텍스트 추가
                        msg = args[0]
                        if self.status_text and self.status_text.winfo_exists():
                            self.status_text.insert("end", msg + "\n")
                            self.status_text.see("end")
                    
                    elif task == "status":
                        # 상태 업데이트 (case_index, display_text, color, emoji_text, bg_color)
                        case_index, display_text, text_color, bg_color = args
                        
                        if case_index in self.case_status and self.case_status[case_index].winfo_exists():
                            self.case_status[case_index].configure(text=display_text, text_color=text_color)
                            
                        if case_index in self.case_frames and self.case_frames[case_index].winfo_exists():
                            if bg_color:
                                self.case_frames[case_index].configure(fg_color=bg_color)
                                for widget in self.case_frames[case_index].winfo_children():
                                    if widget.winfo_exists():
                                        try:
                                            widget.configure(fg_color=bg_color)
                                        except (tk.TclError, AttributeError):
                                            try:
                                                widget.config(bg=bg_color)
                                            except Exception:
                                                pass
                                                
                    elif task == "progress":
                        # 진행률 바 업데이트 (percentage, text_status)
                        percentage, text_status = args
                        if hasattr(self, "progress_var") and self.progress_var:
                            self.progress_var.set(percentage)
                        if hasattr(self, "progress_bar") and self.progress_bar.winfo_exists():
                            self.progress_bar.set(percentage / 100.0)
                        if text_status and self.status_text and self.status_text.winfo_exists():
                            timestamp = datetime.now().strftime("%H:%M:%S")
                            self.status_text.insert("end", f"[{timestamp}] {text_status}\n")
                            self.status_text.see("end")
                            
                    elif task == "function":
                        # 임의의 함수 실행 (버튼 상태 변경 등)
                        func = args[0]
                        func(*args[1:], **kwargs)
                        
                except Exception as e:
                    print(f"UI Queue 처리 중 오류: {e}")
                finally:
                    self.ui_queue.task_done()
                    
        except queue.Empty:
            pass
        finally:
            # 100ms 후 다시 실행되도록 예약
            if hasattr(self, "root") and self.root and self.root.winfo_exists():
                self.root.after(100, self._process_ui_queue)

    def run(self):
        """GUI 실행"""
        # UI 업데이트 큐 프로세서 시작
        self.root.after(100, self._process_ui_queue)
        
        self.root.after(100, self.load_google_sheet)
        self.root.mainloop()


# ---------------------------------------------------------------------------
# 진입점: python batch_gui_maker.py 로 실행 시 gui.main_window.run_app() 호출
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    config.load_user_settings()
    from gui.main_window import run_app
    run_app()

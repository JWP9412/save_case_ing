#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
App Controller (AppController)
==========================

Role: Main controller that assembles ProcessController, panels, and utilities,
and mediates user input.
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import customtkinter as ctk
import gspread
import json
import threading
import queue
import time
import subprocess
import os
import glob
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

import config
from config import (
    COL_WIDTHS,
    COL_NAMES,
    DEFAULT_COL_ORDER,
    COLUMN_ORDER_FILE,
    HEADER_IMAGE_PATH,
    HEADER_BG_COLOR,
)

from services.google_sheets import GoogleSheetsService
from services.puppeteer import PuppeteerService
from services.process_controller import ProcessController
from services.history_manager import HistoryManager
from services.logger_service import setup_logger, register_gui_handler, get_logger
from services.search_manager import find_match_indices
from services import theme_manager as theme_manager_module
from services import update_history as update_history_service
from services import google_oauth

import sys

# Add project root to sys.path for gui/ modules
_gui_dir = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_gui_dir)
if _root and _root not in sys.path:
    sys.path.insert(0, _root)

from gui.dialogs.captcha_dialog import CaptchaInputDialog
from gui.dialogs.settings_dialog import SettingsDialog
from gui.dialogs.find_dialog import FindDialog
from gui.dialogs.sheet_viewer_dialog import SheetViewerDialog
from gui.dialogs.case_list_manage_dialog import CaseListManageDialog
from gui.panels import (
    HeaderPanel,
    ControlPanel,
    SettingsPanel,
    ProgressPanel,
    CaseListPanel,
)
from gui.utils.search_ui import SearchUI
from gui.utils import window_lifecycle as window_lifecycle_module
from gui.utils import window_bootstrap as window_bootstrap_module
from gui.utils import bind_utils as bind_utils_module
from gui.utils import case_list_columns as case_list_columns_module
from gui.utils import google_sheet_ui as sheet_loader_module
from gui.utils import ui_queue_manager as ui_queue_manager_module
from gui.utils import captcha_ui as captcha_ui_module
from gui.utils import selection_manager as selection_manager_module
from gui.utils import email_ui as email_ui_module
from gui.utils import case_list_builder as case_list_builder_module
from gui.utils import history_ui as history_ui_module
from gui.utils import column_resizer as column_resizer_module
from gui.utils import batch_actions as batch_actions_module

try:
    from tksheet import Sheet
    TKSHEET_AVAILABLE = True
except ImportError:
    TKSHEET_AVAILABLE = False
    Sheet = None


class AppController:
    """
    Main controller for batch processing app.
    """

    def __init__(self):
        """Initialize controller. GUI window is created in create_window()."""
        self.root = None
        self.case_list = []
        self.selected_cases = []
        self.processing = False
        self.progress_var = None
        self.status_text = None
        self.case_checkboxes = {}
        self.header_select_all_var = None
        self.processing_thread = None

        self._ui_updating = False
        self._extra_width_last_col = 0
        self.ui_queue = queue.Queue()
        self._file_lock = threading.Lock()

        self.browser_ws_urls = {}
        self.browser_processes = {}

        # 기본 정렬: 최근 업데이트 열(내부 인덱스 9)
        self.sort_column_index = 9
        self.sort_reverse = False
        self._resize_col = None
        self._resize_start_x = None
        self._resize_start_width = None
        self._resize_current_width = None
        self.resize_guide_line = None
        self.col_order = list(DEFAULT_COL_ORDER)
        self.col_widths = list(COL_WIDTHS)
        self._tksheet_warned = False

        self.max_parallel = None
        self.max_retry = None
        self.retry_delay = None
        self._appearance_mode = "Dark"
        self._theme_index = 1
        self._last_search_query = ""
        self._current_search_index = 0

    def get_theme_color(self, key):
        """Return theme color or font. Delegated to theme_manager."""
        return theme_manager_module.get_theme_color(key, self._theme_index)

    def _load_theme_setting(self):
        """Load theme setting. Delegated to theme_manager."""
        return theme_manager_module.load_theme_setting()

    def _save_theme_setting(self, mode):
        """Save theme setting. Delegated to theme_manager."""
        theme_manager_module.save_theme_setting(mode)

    def _apply_theme(self, mode):
        """Apply theme. Delegated to theme_manager."""
        self._appearance_mode = mode
        self._theme_index = theme_manager_module.apply_theme(mode)

    def on_closing(self):
        """Handle window closing. Delegated to window_lifecycle."""
        window_lifecycle_module.handle_window_closing(self)

    def create_window(self):
        """Create main window. Delegated to window_bootstrap after theme application."""
        saved_theme = self._load_theme_setting()
        self._apply_theme(saved_theme)
        return window_bootstrap_module.create_root_and_services(self)

    def create_header(self, parent):
        """Create header. Delegated to HeaderPanel."""
        return HeaderPanel.create(parent, self)

    def create_control_panel(self, parent):
        """Create control panel. Delegated to ControlPanel."""
        frame = ControlPanel.create(parent, self)
        self.root.after(100, self.update_email_btn_text)
        return frame

    def _set_control_btn_state(self, btn, enabled):
        """Set control button state. Delegated to ControlPanel."""
        ControlPanel.set_control_btn_state(self, btn, enabled)

    def _open_settings_dialog(self):
        """Open settings dialog."""
        dlg = SettingsDialog(
            self.root,
            app=self,
            on_save_callback=lambda: self.log_message("Settings saved. Some items apply after restart."),
        )
        dlg.focus_set()

    def ensure_google_linked_on_startup(self):
        """OAuth 모드에서 미연동이면 최초 1회 연동을 안내합니다."""
        mode = str(getattr(config, "GOOGLE_AUTH_MODE", "oauth")).strip().lower()
        if mode != "oauth":
            return
        if google_oauth.has_valid_token():
            return
        should_link = messagebox.askyesno(
            "Google 계정 연동",
            "처음 사용을 위해 Google 계정 연동이 필요합니다.\n\n"
            "지금 연동하시겠습니까?\n"
            "- 시트 읽기/쓰기\n"
            "- 기일 캘린더 등록",
            parent=self.root,
        )
        if not should_link:
            self.log_message("⚠️ Google OAuth 연동을 건너뛰었습니다. 서비스 계정으로만 시도합니다.")
            return
        try:
            google_oauth.get_credentials(interactive=True, log_callback=self.log_message)
            self.log_message("✅ Google 계정 연동 완료")
        except Exception as e:
            messagebox.showwarning(
                "Google 연동 실패",
                f"Google 연동에 실패했습니다.\n{e}\n\n"
                "서비스 계정으로 계속 시도합니다.",
                parent=self.root,
            )

    def create_settings_panel(self, parent):
        """Create settings panel. Delegated to SettingsPanel."""
        return SettingsPanel.create(parent, self)

    def _sync_spin(self, entry_widget, int_var, low, high):
        """Sync entry value with IntVar within range [low, high]."""
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
        """Create case list panel. Delegated to CaseListPanel."""
        frame = CaseListPanel.create(parent, self)
        self._search_ui = SearchUI(self)
        return frame

    def _clear_find_highlights(self):
        if getattr(self, "_search_ui", None):
            self._search_ui.clear_find_highlights()

    def _apply_find_highlight(self, row_index, q):
        if getattr(self, "_search_ui", None):
            self._search_ui.apply_find_highlight(row_index, q)

    def _scroll_to_row_and_highlight(self, row_index, query):
        if getattr(self, "_search_ui", None):
            self._search_ui.scroll_to_row_and_highlight(row_index, query)

    def update_search_count(self):
        """Update search count label. Delegated to search_ui."""
        if getattr(self, "_search_ui", None):
            self._search_ui.update_search_count()

    def perform_search(self, query=None, direction="next"):
        """Perform search. Delegated to search_ui."""
        if getattr(self, "_search_ui", None):
            self._search_ui.perform_search(query=query, direction=direction)

    def _bind_mousewheel_recursive(self, widget, handler):
        """Bind mousewheel handler recursively. Delegated to bind_utils."""
        bind_utils_module.bind_mousewheel_recursive(widget, handler)

    def _bind_mousewheel_to_case_list(self):
        """Bind mousewheel to case list. Delegated to bind_utils."""
        if not hasattr(self, "_case_list_mousewheel_handler") or not hasattr(
            self, "case_list_frame"
        ):
            return
        bind_utils_module.bind_mousewheel_to_case_list(
            self.case_list_frame, self._case_list_mousewheel_handler
        )

    def _open_column_order_dialog(self):
        """Open column order dialog. Delegated to case_list_columns."""
        case_list_columns_module.open_column_order_dialog(self)

    def _open_case_list_manage_dialog(self):
        """Open case list manage dialog (add/edit/delete/hide/unhide)."""
        if (
            getattr(self, "_case_list_manage_dialog", None) is not None
            and self._case_list_manage_dialog.winfo_exists()
        ):
            self._case_list_manage_dialog.focus_set()
            return
        self._case_list_manage_dialog = CaseListManageDialog(self.root, self)
        self._case_list_manage_dialog.focus_set()

    def _open_find_dialog(self, event=None):
        """Open find dialog."""
        if (
            getattr(self, "_find_dialog", None) is not None
            and self._find_dialog.winfo_exists()
        ):
            self._find_dialog.focus_set()
            return "break"

        match_indices = []
        current_index = [0]

        def on_find(query):
            self._clear_find_highlights()
            match_indices[:] = find_match_indices(getattr(self, "case_list", []), query)
            current_index[0] = 0
            if not match_indices:
                messagebox.showinfo("Find", "No matches found.", parent=self._find_dialog)
                return
            self._scroll_to_row_and_highlight(match_indices[0], query)

        def on_next(query):
            self._clear_find_highlights()
            match_indices[:] = find_match_indices(getattr(self, "case_list", []), query)
            if not match_indices:
                messagebox.showinfo("Find", "No matches found.", parent=self._find_dialog)
                return
            current_index[0] = (current_index[0] + 1) % len(match_indices)
            self._scroll_to_row_and_highlight(match_indices[current_index[0]], query)

        def on_close():
            self._clear_find_highlights()
            self._find_dialog = None

        self._find_dialog = FindDialog(self.root, on_find, on_next, on_close)
        return "break"

    def create_progress_panel(self, parent):
        """Create progress panel. Delegated to ProgressPanel."""
        frame = ProgressPanel.create(parent, self)
        register_gui_handler(self)
        return frame

    def reset_internal_data(self):
        """Reset internal data. Delegated to case_list_builder."""
        case_list_builder_module.reset_internal_data(self)

    def sort_case_list(self):
        """Sort case list. Delegated to case_list_columns."""
        case_list_columns_module.sort_case_list(self)

    def on_header_click(self, col_idx):
        """Handle header click for sorting. Delegated to case_list_columns."""
        case_list_columns_module.on_header_click(self, col_idx)

    def load_google_sheet(self, force_network=False):
        """Load Google Sheet data. force_network=False면 캐시 우선, True면 구글 시트에서 조회. Delegated to sheet_loader."""
        sheet_loader_module.load_google_sheet(self, force_network)

    def _display_width_up_to(self, display_idx):
        """Return cumulative width up to display_idx."""
        return sum(self.col_widths[self.col_order[i]] for i in range(display_idx + 1))

    def _get_effective_widths(self):
        """Return total width and extra width for last column."""
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
        """Create list header. Delegated to CaseListPanel."""
        CaseListPanel.create_list_header(self)

    def _on_resize_press(self, display_idx, event):
        """Handle resize drag start. Delegated to column_resizer."""
        column_resizer_module.on_resize_press(self, display_idx, event)

    def _on_resize_motion(self, display_idx, event):
        """Handle resize drag motion. Delegated to column_resizer."""
        column_resizer_module.on_resize_motion(self, display_idx, event)

    def _on_resize_release(self, event):
        """Handle resize drag release. Delegated to column_resizer."""
        column_resizer_module.on_resize_release(self, event)

    def apply_column_width(self, display_idx):
        """Apply column width after resize. Delegated to column_resizer."""
        column_resizer_module.apply_column_width(self, display_idx)

    def create_case_row(self, parent, case, index, total_width, initial_status=None):
        """Create single case row. Delegated to CaseListPanel."""
        from gui.panels import CaseListPanel
        return CaseListPanel.create_case_row(
            self, parent, case, index, total_width, initial_status
        )

    def _validate_captcha_entry(self, index):
        """Validate captcha entry (6 digits). Delegated to captcha_ui."""
        captcha_ui_module.validate_captcha_entry(self, index)

    def update_case_list_ui(self):
        """Update case list UI. Delegated to case_list_builder."""
        case_list_builder_module.update_case_list_ui(self)

    def _on_ui_update_complete(self):
        """Finish UI update. Delegated to case_list_builder."""
        case_list_builder_module._on_ui_update_complete(self)

    def _on_header_select_toggle(self):
        """Toggle header select all. Delegated to case_list_columns."""
        case_list_columns_module.on_header_select_toggle(self)

    def _open_sheet_viewer(self, case_index):
        """Open sheet viewer for a case."""
        if case_index < 0 or case_index >= len(self.case_list):
            return
        
        if not TKSHEET_AVAILABLE:
            if not getattr(self, "_tksheet_warned", False):
                self._tksheet_warned = True
                messagebox.showwarning(
                    "Library Missing",
                    "tksheet is not installed. Please run 'pip install tksheet'.",
                )
            return

        SheetViewerDialog(
            self.root,
            self.case_list[case_index],
            self.google_sheets_service,
            self.get_theme_color
        )

    def select_all_cases(self):
        """Select all cases. Delegated to selection_manager."""
        selection_manager_module.select_all_cases(self)

    def deselect_all_cases(self):
        """Deselect all cases. Delegated to selection_manager."""
        selection_manager_module.deselect_all_cases(self)

    def get_selected_cases(self):
        """Return list of selected cases. Delegated to selection_manager."""
        return selection_manager_module.get_selected_cases(self)

    def on_checkbox_change(self, index):
        """Handle checkbox change. Delegated to selection_manager."""
        selection_manager_module.on_checkbox_change(self, index)

    def start_batch_processing(self):
        """Start batch processing. Delegated to ProcessController."""
        selected_cases_with_index = self.get_selected_cases()
        selected_cases = [case for _, case in selected_cases_with_index]
        self.process_controller.start_processing(selected_cases)

    def stop_batch_processing(self):
        """Stop batch processing. Delegated to ProcessController."""
        self.process_controller.stop_processing()

    def cleanup_case_process(self, case_number):
        """Cleanup individual case process. Delegated to ProcessController."""
        self.process_controller.cleanup_case_process(case_number)

    def _lane_for_case(self, case_number, n_lanes):
        """Return lane index for a case. Delegated to ProcessController."""
        return self.process_controller._lane_for_case(case_number, n_lanes)

    def get_case_profile_index(self, case_number):
        """Return profile index for a case. Delegated to ProcessController."""
        return self.process_controller.get_case_profile_index(case_number)

    def execute_actual_processing(self, cases):
        """Execute actual processing. Delegated to ProcessController."""
        self.process_controller.execute_actual_processing(cases)

    def _check_and_prompt_failed_cases(self, processed_cases):
        """Check and prompt for failed cases. Delegated to ProcessController."""
        self.process_controller._check_and_prompt_failed_cases(processed_cases)

    def _process_auto_case(self, case, case_index):
        """Process auto case. Delegated to ProcessController."""
        return self.process_controller._process_auto_case(case, case_index)

    def process_single_case_parallel(self, case, case_index, instance_index=0):
        """Process single case in parallel. Delegated to ProcessController."""
        return self.process_controller.process_single_case_parallel(case, case_index, instance_index)

    def get_captcha_input(self, case_index):
        """Get captcha input. Delegated to captcha_ui."""
        return captcha_ui_module.get_captcha_input(self, case_index)

    def set_captcha_input(self, case_index, text, lock_after=True):
        """Set captcha input (thread-safe). Delegated to captcha_ui."""
        captcha_ui_module.set_captcha_input(self, case_index, text, lock_after=lock_after)

    def set_captcha_entry_locked(self, case_index, locked):
        """Lock/unlock captcha entry. Delegated to captcha_ui."""
        captcha_ui_module.set_captcha_entry_locked(self, case_index, locked)

    def on_captcha_enter(self, case_index):
        """Handle captcha enter. Delegated to captcha_ui."""
        captcha_ui_module.on_captcha_enter(self, case_index)

    def move_to_next_input(self, current_case_index):
        """Move focus to next input. Delegated to captcha_ui."""
        captcha_ui_module.move_to_next_input(self, current_case_index)

    def start_processing_thread(self):
        """Start processing thread."""
        processing_thread = threading.Thread(
            target=self.process_all_captcha_inputs, daemon=True
        )
        processing_thread.start()
        self.log_message("Background processing started.")

    def _process_one_case(
        self, original_index, case, total_cases, total_start_time, selected_cases
    ):
        """Process one case. Delegated to ProcessController."""
        return self.process_controller._process_one_case(
            original_index, case, total_cases, total_start_time, selected_cases
        )

    def process_all_captcha_inputs(self):
        """Process all captcha inputs. Delegated to ProcessController."""
        self.process_controller.process_all_captcha_inputs()

    def capture_captcha_image(self, case_number, defendant, court, instance_index=0):
        """Capture captcha image. Delegated to ProcessController."""
        return self.process_controller.capture_captcha_image(
            case_number, defendant, court, instance_index
        )

    def execute_case_processing_with_captcha(self, case, case_index, instance_index=0):
        """Execute processing with captcha. Delegated to ProcessController."""
        return self.process_controller.execute_case_processing_with_captcha(
            case, case_index, instance_index
        )

    def parse_puppeteer_result(self, stdout):
        """Parse Puppeteer execution result."""
        try:
            image_path = None
            for line in stdout.split("\n"):
                if "GUI_IMAGE_PATH:" in line:
                    image_path = line.split("GUI_IMAGE_PATH: ")[1].strip()
                    break

            if "case_result_" in stdout:
                result_files = glob.glob("results/case_result_*.json")
                if result_files:
                    latest_file = max(result_files, key=os.path.getctime)
                    with open(latest_file, "r", encoding="utf-8") as f:
                        result_data = json.load(f)
                    if image_path:
                        result_data["image_path"] = image_path
                    return result_data

            return {"success": True, "message": "Processing complete", "image_path": image_path}
        except Exception as e:
            self.log_message(f"Result parsing error: {e}")
            return {"success": False, "message": str(e)}

    def execute_case_processing(self, case, captcha_input):
        """Execute case processing. Delegated to ProcessController."""
        return self.process_controller.execute_case_processing(case, captcha_input)

    def extract_progress_from_result(self, case_number):
        """Extract progress data from result JSON. Delegated to puppeteer_service."""
        return self.puppeteer_service.extract_progress_from_result(case_number)

    def load_update_history(self):
        """Load update history. Delegated to update_history_service."""
        try:
            with getattr(self, "_file_lock", threading.Lock()):
                return update_history_service.load_update_history(
                    config.UPDATE_HISTORY_FILE
                )
        except Exception as e:
            self.log_message(f"Failed to load update history: {e}")
            return {}

    def save_update_history(self, history):
        """Save update history. Delegated to update_history_service."""
        try:
            with getattr(self, "_file_lock", threading.Lock()):
                update_history_service.save_update_history(
                    history, config.UPDATE_HISTORY_FILE
                )
        except Exception as e:
            self.log_message(f"Failed to save update history: {e}")

    def update_case_timestamp(self, case, original_index=None, row_count=0, is_auto=False, hearing_info=None):
        """Update case timestamp. Delegated to history_ui."""
        history_ui_module.update_case_timestamp(
            self, case, original_index=original_index, row_count=row_count, is_auto=is_auto, hearing_info=hearing_info
        )

    def get_days_since_update(self, case):
        """Return days since last update. Delegated to update_history_service."""
        history = self.load_update_history()
        return update_history_service.get_days_since_update(case, history)

    def get_days_until_hearing(self, hearing_info):
        """기일 문자열에서 오늘로부터 기일까지의 일수. Delegated to update_history_service."""
        return update_history_service.get_days_until_hearing(hearing_info)

    def load_column_widths(self):
        """Load column widths. Delegated to case_list_columns."""
        return case_list_columns_module.load_column_widths()

    def load_column_order(self):
        """Load column order. Delegated to case_list_columns."""
        return case_list_columns_module.load_column_order()

    def _save_column_order(self):
        """Save current column order. Delegated to case_list_columns."""
        case_list_columns_module.save_column_order(self)

    def _save_column_widths(self):
        """Save current column widths. Delegated to case_list_columns."""
        case_list_columns_module.save_column_widths(self)

    def save_to_google_sheets(self, case, result_data):
        """Save results to Google Sheets. Delegated to ProcessController."""
        return self.process_controller.save_to_google_sheets(case, result_data)

    def update_case_status(self, case_index, status, color, emoji=""):
        """Update case status. Delegated to ui_queue_manager."""
        ui_queue_manager_module.update_case_status(self, case_index, status, color, emoji)

    def update_captcha_image(self, case_index, image_path):
        """Update captcha image. Delegated to captcha_ui."""
        return captcha_ui_module.update_captcha_image(self, case_index, image_path)

    def wait_for_captcha_input(self, case_index, timeout_seconds=300):
        """Wait for captcha input. Delegated to captcha_ui."""
        return captcha_ui_module.wait_for_captcha_input(self, case_index, timeout_seconds)

    def find_case_index(self, case_number):
        """Find case index by case number. Delegated to selection_manager."""
        return selection_manager_module.find_case_index(self, case_number)

    def update_email_btn_text(self):
        """Update email button text. Delegated to email_ui."""
        email_ui_module.update_email_btn_text(self)

    def send_notification_email(self):
        """Send notification email. Delegated to email_ui."""
        email_ui_module.send_notification_email(self)

    def remove_duplicates_for_selected_cases(self):
        """선택 사건 중복 제거. Delegated to batch_actions."""
        batch_actions_module.remove_duplicates_for_selected_cases(self)

    def reset_and_refetch_selected_cases(self):
        """선택 사건 기록 초기화·재수집. Delegated to batch_actions."""
        batch_actions_module.reset_and_refetch_selected_cases(self)

    def processing_completed(self):
        """Finish processing. Delegated to ui_queue_manager."""
        ui_queue_manager_module.processing_completed(self)

    def log_message(self, message):
        """Log message. Delegated to standard logger."""
        get_logger().info("%s", message)

    def update_progress(self, percentage, status_text=""):
        """Update progress bar. Delegated to ui_queue_manager."""
        ui_queue_manager_module.update_progress(self, percentage, status_text)

    def show_warning(self, message):
        """Show warning dialog. Called from ProcessController (main or via ui_queue)."""
        messagebox.showwarning("경고", message)

    def show_info(self, message):
        """Show info dialog. Called from ProcessController (main or via ui_queue)."""
        messagebox.showinfo("알림", message)

    def ask_yesno(self, title, message):
        """Show yes/no dialog. Returns True/False. Called from ProcessController (main or via ui_queue)."""
        return messagebox.askyesno(title, message)

    def get_case_status_text(self, case_index):
        """Return current status label text for case. Used by ProcessController for email result grouping."""
        if case_index not in getattr(self, "case_status", {}):
            return ""
        try:
            return self.case_status[case_index].cget("text") or ""
        except Exception:
            return ""

    def update_auto_search_label(self, case_number):
        """Update the '자동 조회' column label to '자동 가능' after a successful search. Called from ProcessController via ui_queue."""
        case_index = self.find_case_index(case_number)
        if case_index == -1:
            return
        labels = getattr(self, "case_record_labels", {})
        if case_index not in labels:
            return
        lbl = labels[case_index]
        if lbl and getattr(lbl, "winfo_exists", lambda: False)() and lbl.winfo_exists():
            try:
                lbl.configure(text="자동 가능", text_color=self.get_theme_color("success"))
            except Exception:
                pass

    def _process_ui_queue(self):
        """Process UI update queue. Delegated to ui_queue_manager."""
        ui_queue_manager_module.process_ui_queue(self)

    def run(self):
        """Start GUI event loop. 캐시가 있으면 창을 띄우기 전에 목록을 그려 두어, 열리자마자 사건 항목이 보이도록 함."""
        self.root.after(100, self._process_ui_queue)
        self.ensure_google_linked_on_startup()

        cached = sheet_loader_module.load_case_list_cache()
        if cached is not None:
            self.root.withdraw()
            self.root.update()
            self.reset_internal_data()
            sheet_loader_module._apply_loaded_data_to_app(self, cached)
            self.log_message(f"캐시에서 {len(cached)}개 사건 로드")
            self.root.deiconify()
        else:
            self.root.after(100, self.load_google_sheet)

        self.root.mainloop()

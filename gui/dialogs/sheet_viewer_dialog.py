# -*- coding: utf-8 -*-
"""
시트 뷰어 다이얼로그
====================

역할: 해당 사건의 구글 시트 진행내역을 tksheet 그리드로 표시하고, 편집 후 구글 시트에 저장할 수 있습니다.
호출: 사건 목록 각 행의 '시트' 버튼 클릭 시 BatchProcessingGUI에서 띄웁니다.
tksheet 미설치 시 경고 메시지를 띄우고 창을 열지 않습니다.
"""
import tkinter as tk
from tkinter import messagebox
import threading
import customtkinter as ctk

try:
    from tksheet import Sheet
    TKSHEET_AVAILABLE = True
except ImportError:
    TKSHEET_AVAILABLE = False
    Sheet = None


class SheetViewerDialog(tk.Toplevel):
    def __init__(self, parent, case_data, google_sheets_service, theme_color_getter):
        if not TKSHEET_AVAILABLE:
            messagebox.showwarning(
                "라이브러리 없음",
                "tksheet가 설치되지 않았습니다.\n"
                "pip install tksheet 실행 후 프로그램을 다시 실행하세요.",
                parent=parent
            )
            # Toplevel 생성 실패 처리가 애매하므로, 그냥 닫히도록 함
            # 실제로는 호출 측에서 TKSHEET_AVAILABLE 체크를 먼저 하는 것이 좋음
            return

        super().__init__(parent)
        self.case_data = case_data
        self.google_sheets_service = google_sheets_service
        self.theme_color_getter = theme_color_getter
        
        case_number = case_data.get("사건번호", "")
        self.title(f"시트 보기: {case_number}")
        self.geometry("900x500")
        self.minsize(400, 300)
        
        self.sheet_widget = None
        self._create_widgets()
        self._load_data()

    def _create_widgets(self):
        top_bar = tk.Frame(self)
        top_bar.pack(fill=tk.X, padx=5, pady=5)
        
        self.save_btn = tk.Button(
            top_bar,
            text="💾 구글 시트에 저장",
            font=self.theme_color_getter("font_small"),
            command=self._do_save,
        )
        self.save_btn.pack(side=tk.LEFT)

        self.loading_label = tk.Label(
            self, text="로딩 중...", font=self.theme_color_getter("font_small")
        )
        self.loading_label.pack(expand=True)

        self.sheet_container = tk.Frame(self)

    def _load_data(self):
        def fetch():
            try:
                data = self.google_sheets_service.get_full_sheet_data(self.case_data)
                err = None
            except Exception as e:
                data = None
                err = str(e)
            self.after(0, lambda: self._apply_load(data, err))

        threading.Thread(target=fetch, daemon=True).start()

    def _apply_load(self, data, err):
        if err:
            self.loading_label.destroy()
            messagebox.showerror("시트 로드 실패", err, parent=self)
            return
            
        self.loading_label.destroy()
        self.sheet_container.pack(fill=tk.BOTH, expand=True)
        
        sh = Sheet(
            self.sheet_container,
            data=data if data else [],
            headers=0,
        )
        sh.enable_bindings()
        sh.pack(fill=tk.BOTH, expand=True)
        self.sheet_widget = sh

    def _get_sheet_data_for_save(self):
        if not self.sheet_widget:
            return []
        for method_name in ("get_sheet_data", "get_data"):
            m = getattr(self.sheet_widget, method_name, None)
            if callable(m):
                try:
                    out = m()
                    if isinstance(out, list):
                        return out
                except Exception:
                    continue
        return []

    def _do_save(self):
        current = self._get_sheet_data_for_save()
        if not current:
            messagebox.showinfo("저장", "저장할 데이터가 없습니다.", parent=self)
            return
            
        self.save_btn.configure(state="disabled", text="저장 중...")

        def save_thread():
            ok = self.google_sheets_service.overwrite_sheet_data(self.case_data, current)
            self.after(0, lambda: self._save_done(ok))

        threading.Thread(target=save_thread, daemon=True).start()

    def _save_done(self, ok):
        self.save_btn.configure(state="normal", text="💾 구글 시트에 저장")
        if ok:
            messagebox.showinfo("저장", "구글 시트에 저장되었습니다.", parent=self)
        else:
            messagebox.showerror("저장 실패", "구글 시트 저장에 실패했습니다.", parent=self)

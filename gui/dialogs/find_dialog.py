# -*- coding: utf-8 -*-
"""
찾기 다이얼로그
===============

역할: 사건 목록에서 검색어와 일치하는 행을 찾고, 다음 찾기로 이동합니다.
호출: Ctrl+F 단축키 또는 메뉴에서 찾기 선택 시 BatchProcessingGUI에서 띄웁니다.
콜백으로 on_find(첫 검색), on_next(다음), on_close(닫기)를 앱에 전달합니다.
"""
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk


class FindDialog(ctk.CTkToplevel):
    def __init__(self, parent, on_find_callback, on_next_callback, on_close_callback):
        super().__init__(parent)
        self.title("찾기")
        self.geometry("400x140")
        self.transient(parent)
        self.resizable(False, False)
        
        self.on_find_callback = on_find_callback
        self.on_next_callback = on_next_callback
        self.on_close_callback = on_close_callback
        
        self._create_widgets()
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _create_widgets(self):
        frm = ctk.CTkFrame(self, fg_color="transparent")
        frm.pack(fill=tk.BOTH, expand=True, padx=14, pady=14)

        ctk.CTkLabel(frm, text="검색어:").pack(anchor=tk.W)
        self.entry_var = tk.StringVar()
        entry = ctk.CTkEntry(frm, textvariable=self.entry_var, width=320, height=32)
        entry.pack(fill=tk.X, pady=(0, 10))
        entry.focus_set()
        
        btn_frm = ctk.CTkFrame(frm, fg_color="transparent")
        btn_frm.pack(fill=tk.X, pady=(4, 0))
        
        ctk.CTkButton(
            btn_frm, text="찾기", width=100,
            command=self._on_find
        ).pack(side=tk.LEFT, padx=(0, 8))
        
        ctk.CTkButton(
            btn_frm, text="다음 찾기", width=100,
            command=self._on_next
        ).pack(side=tk.LEFT)

    def _on_find(self):
        self.on_find_callback(self.entry_var.get())

    def _on_next(self):
        self.on_next_callback(self.entry_var.get())

    def _on_closing(self):
        self.on_close_callback()
        self.destroy()

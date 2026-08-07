# -*- coding: utf-8 -*-
"""
특정 기간 조회 다이얼로그
========================

시작일·종료일을 입력(자유 형식)하거나 달력으로 고릅니다.
기본값: 어제 ~ 오늘.
"""
from __future__ import annotations

import tkinter as tk
from datetime import date
from tkinter import messagebox

import customtkinter as ctk

from gui.dialogs.date_picker import DatePickerPopup
from services.date_utils import (
    format_date,
    last_n_days,
    parse_date,
    this_month,
    yesterday_today,
)


class PeriodQueryDialog(ctk.CTkToplevel):
    """
    기간 입력 창.
    확인 시 result = (start_date, end_date) 를 갖고, 취소/닫기 시 None.
    """

    def __init__(self, parent, title="특정 기간 조회"):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.result = None
        self.transient(parent)
        self.grab_set()

        start, end = yesterday_today()
        self._build(start, end)
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.after(50, self._center)

    def _center(self):
        try:
            self.update_idletasks()
            w, h = self.winfo_width(), self.winfo_height()
            sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
            self.geometry(f"+{(sw - w) // 2}+{(sh - h) // 2}")
        except Exception:
            pass

    def _build(self, start: date, end: date):
        pad = {"padx": 12, "pady": 6}
        ctk.CTkLabel(
            self,
            text="조회할 기간을 입력하세요.\n(예: 26.08.06. / 2026/ 8/ 6 / 20260806)",
            font=ctk.CTkFont(family="맑은 고딕", size=13),
            justify=tk.LEFT,
        ).pack(anchor=tk.W, **pad)

        # 시작일
        row_s = ctk.CTkFrame(self, fg_color="transparent")
        row_s.pack(fill=tk.X, **pad)
        ctk.CTkLabel(row_s, text="시작일", width=60).pack(side=tk.LEFT)
        self.start_entry = ctk.CTkEntry(row_s, width=160)
        self.start_entry.pack(side=tk.LEFT, padx=(4, 4))
        self.start_entry.insert(0, format_date(start))
        self.start_entry.bind("<FocusOut>", lambda e: self._normalize_entry(self.start_entry))
        ctk.CTkButton(
            row_s, text="달력", width=56,
            command=lambda: self._open_cal(self.start_entry),
        ).pack(side=tk.LEFT)

        # 종료일
        row_e = ctk.CTkFrame(self, fg_color="transparent")
        row_e.pack(fill=tk.X, **pad)
        ctk.CTkLabel(row_e, text="종료일", width=60).pack(side=tk.LEFT)
        self.end_entry = ctk.CTkEntry(row_e, width=160)
        self.end_entry.pack(side=tk.LEFT, padx=(4, 4))
        self.end_entry.insert(0, format_date(end))
        self.end_entry.bind("<FocusOut>", lambda e: self._normalize_entry(self.end_entry))
        ctk.CTkButton(
            row_e, text="달력", width=56,
            command=lambda: self._open_cal(self.end_entry),
        ).pack(side=tk.LEFT)

        # 프리셋
        presets = ctk.CTkFrame(self, fg_color="transparent")
        presets.pack(fill=tk.X, **pad)
        ctk.CTkButton(
            presets, text="어제~오늘", width=90,
            command=lambda: self._apply_range(*yesterday_today()),
        ).pack(side=tk.LEFT, padx=(0, 6))
        ctk.CTkButton(
            presets, text="최근 7일", width=90,
            command=lambda: self._apply_range(*last_n_days(7)),
        ).pack(side=tk.LEFT, padx=(0, 6))
        ctk.CTkButton(
            presets, text="이번 달", width=90,
            command=lambda: self._apply_range(*this_month()),
        ).pack(side=tk.LEFT)

        # 확인/취소
        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(fill=tk.X, padx=12, pady=(8, 12))
        ctk.CTkButton(btns, text="취소", width=90, command=self._on_cancel).pack(
            side=tk.RIGHT, padx=(6, 0)
        )
        ctk.CTkButton(btns, text="확인", width=90, command=self._on_ok).pack(
            side=tk.RIGHT
        )

    def _apply_range(self, start: date, end: date):
        self.start_entry.delete(0, tk.END)
        self.start_entry.insert(0, format_date(start))
        self.end_entry.delete(0, tk.END)
        self.end_entry.insert(0, format_date(end))

    def _normalize_entry(self, entry):
        raw = entry.get()
        d = parse_date(raw)
        if d is None:
            return
        entry.delete(0, tk.END)
        entry.insert(0, format_date(d))

    def _open_cal(self, entry):
        cur = parse_date(entry.get()) or date.today()

        def _on_pick(d):
            entry.delete(0, tk.END)
            entry.insert(0, format_date(d))

        DatePickerPopup(self, initial=cur, on_select=_on_pick)

    def _on_ok(self):
        start = parse_date(self.start_entry.get())
        end = parse_date(self.end_entry.get())
        if start is None:
            messagebox.showwarning("기간 조회", "시작일을 인식할 수 없습니다.", parent=self)
            return
        if end is None:
            messagebox.showwarning("기간 조회", "종료일을 인식할 수 없습니다.", parent=self)
            return
        if start > end:
            messagebox.showwarning(
                "기간 조회", "시작일이 종료일보다 늦습니다.", parent=self
            )
            return
        # 정규화 표시
        self.start_entry.delete(0, tk.END)
        self.start_entry.insert(0, format_date(start))
        self.end_entry.delete(0, tk.END)
        self.end_entry.insert(0, format_date(end))
        self.result = (start, end)
        self.destroy()

    def _on_cancel(self):
        self.result = None
        self.destroy()


def ask_period_range(parent):
    """
    기간 다이얼로그를 띄우고 (start, end) 또는 None 을 반환합니다.
    모달(wait_window)로 동작합니다.
    """
    dlg = PeriodQueryDialog(parent)
    parent.wait_window(dlg)
    return dlg.result
